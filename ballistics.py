"""Ballistic math for Squad Ballistics.

Pure functions only (no Qt), so everything here can be unit-tested.

Projectile model (same idea as the game and SquadCalc): no air drag, a
per-weapon gravity scale and an optional phase right after launch during
which the projectile speeds up (rocket motor, positive acceleration) or
slows down (UB-32 rockets, negative acceleration).

The changing speed is folded into an "equivalent velocity": the constant
speed that covers the distance in the same time. For the low, flat shots
these weapons are used for this gives the correct drop at the target.
"""

import json
import math
from dataclasses import dataclass, field

# Squad's world gravity in m/s^2 (same value SquadCalc uses).
GRAVITY = 9.78

# Squad mortars use the 6400 mil circle.
MILS_PER_DEGREE = 6400 / 360

ARCS = ("low", "high")
UNITS = ("deg", "mil")
AIMS = ("overlay", "elevation")


class WeaponDataError(ValueError):
    """Raised when weapons.json contains invalid data."""


@dataclass(frozen=True)
class Weapon:
    name: str
    velocity: float
    gravity: float = 1.0
    arc: str = "low"
    unit: str = "deg"
    aim: str = "overlay"
    angle_offset: float = 0.0
    acceleration: float = 0.0
    acceleration_time: float = 0.0
    min_distance: float = 0.0
    elevation_limits: tuple = (-90.0, 90.0)
    category: str = "other"
    note: str = ""
    note_ru: str = ""
    mod: str = ""

    @classmethod
    def from_dict(cls, name, data):
        if not isinstance(data, dict):
            raise WeaponDataError(f"{name}: entry must be an object")

        if "velocity" not in data:
            raise WeaponDataError(f"{name}: 'velocity' is required")

        def number(key, default):
            value = data.get(key, default)
            if isinstance(value, bool):
                raise WeaponDataError(f"{name}: '{key}' must be a number")
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise WeaponDataError(f"{name}: '{key}' must be a number")
            if not math.isfinite(value):
                raise WeaponDataError(f"{name}: '{key}' must be finite")
            return value

        velocity = number("velocity", 0)
        gravity = number("gravity", 1.0)

        # "deceleration" is the older spelling of a negative acceleration.
        acceleration = (
            number("acceleration", 0.0) - number("deceleration", 0.0)
        )
        acceleration_time = number(
            "acceleration_time",
            data.get("deceleration_time", 0.0)
        )

        if velocity <= 0:
            raise WeaponDataError(f"{name}: 'velocity' must be > 0")
        if gravity < 0:
            raise WeaponDataError(f"{name}: 'gravity' must be >= 0")
        if acceleration_time < 0:
            raise WeaponDataError(f"{name}: 'acceleration_time' must be >= 0")
        if velocity + acceleration * acceleration_time <= 0:
            raise WeaponDataError(
                f"{name}: deceleration would stop the projectile"
            )

        arc = data.get("arc", "low")
        if arc not in ARCS:
            raise WeaponDataError(f"{name}: 'arc' must be one of {ARCS}")

        unit = data.get("unit", "deg")
        if unit not in UNITS:
            raise WeaponDataError(f"{name}: 'unit' must be one of {UNITS}")

        aim = data.get("aim", "elevation" if arc == "high" else "overlay")
        if aim not in AIMS:
            raise WeaponDataError(f"{name}: 'aim' must be one of {AIMS}")

        limits = data.get("elevation_limits", [-90, 90])
        try:
            low, high = (float(v) for v in limits)
        except (TypeError, ValueError):
            raise WeaponDataError(
                f"{name}: 'elevation_limits' must be [min, max]"
            )
        if low >= high:
            raise WeaponDataError(f"{name}: invalid 'elevation_limits'")

        return cls(
            name=name,
            velocity=velocity,
            gravity=gravity,
            arc=arc,
            unit=unit,
            aim=aim,
            angle_offset=number("angle_offset", 0.0),
            acceleration=acceleration,
            acceleration_time=acceleration_time,
            min_distance=number("min_distance", 0.0),
            elevation_limits=(low, high),
            category=str(data.get("category", "other")),
            note=str(data.get("note", "")),
            note_ru=str(data.get("note_ru", "")),
            mod=str(data.get("mod", "")),
        )

    @property
    def g(self):
        return GRAVITY * self.gravity

    @property
    def has_boost(self):
        return self.acceleration != 0 and self.acceleration_time > 0

    @property
    def boost_distance(self):
        t = self.acceleration_time
        return self.velocity * t + 0.5 * self.acceleration * t * t

    @property
    def cruise_velocity(self):
        return self.velocity + self.acceleration * self.acceleration_time

    def time_to(self, distance):
        """Time to cover `distance` metres along the flight path."""
        if distance <= 0:
            return 0.0

        if not self.has_boost:
            return distance / self.velocity

        if distance <= self.boost_distance:
            a = self.acceleration
            root = math.sqrt(
                max(0.0, self.velocity ** 2 + 2 * a * distance)
            )
            return (root - self.velocity) / a

        return (
            self.acceleration_time
            + (distance - self.boost_distance) / self.cruise_velocity
        )

    def velocity_at(self, distance):
        """Equivalent constant velocity over `distance`."""
        if distance <= 0 or not self.has_boost:
            return self.velocity

        return distance / self.time_to(distance)

    def max_range(self):
        """Maximum range on flat ground (45 degrees), inf without gravity."""
        if self.g == 0:
            return math.inf

        if not self.has_boost:
            return self.velocity ** 2 / self.g

        # Range is reachable while v(d)^2 >= g * d.
        def reachable(d):
            return self.velocity_at(d) ** 2 >= self.g * d

        low, high = 0.0, max(self.velocity, self.cruise_velocity) ** 2 / self.g
        while reachable(high):
            high *= 2

        for _ in range(60):
            mid = (low + high) / 2
            if reachable(mid):
                low = mid
            else:
                high = mid

        return low


@dataclass
class Solution:
    reachable: bool
    arc: str
    distance: float
    height_diff: float
    angle: float = math.nan          # elevation in degrees, angle_offset applied
    raw_angle: float = math.nan      # physical barrel angle in degrees
    mils: float = math.nan
    time_of_flight: float = math.nan
    velocity: float = math.nan
    apex: float = math.nan           # highest point above the weapon, metres
    impact_angle: float = math.nan   # descent angle at the target, degrees
    reason: str = ""
    reason_code: str = ""
    alternatives: dict = field(default_factory=dict)


def resolve_arc(weapon, arc):
    if arc in (None, "", "auto"):
        return weapon.arc
    if arc not in ARCS:
        raise ValueError(f"Unknown arc '{arc}'")
    return arc


def _path(v, g, rad, x):
    """Height of a parabolic path at horizontal distance x."""
    if g == 0:
        return x * math.tan(rad)
    return x * math.tan(rad) - g * x * x / (2 * v * v * math.cos(rad) ** 2)


def solve(weapon, distance, height_diff=0.0, arc=None):
    """Elevation needed to hit a target.

    distance     -- horizontal distance to the target in metres
    height_diff  -- target height relative to the weapon (positive = higher)
    arc          -- "low", "high" or None/"auto" for the weapon default
    """
    arc = resolve_arc(weapon, arc)

    if not math.isfinite(distance) or distance <= 0:
        raise ValueError("Distance must be greater than 0")
    if not math.isfinite(height_diff):
        raise ValueError("Height difference must be a number")

    result = Solution(
        reachable=False,
        arc=arc,
        distance=distance,
        height_diff=height_diff,
    )

    if distance < weapon.min_distance:
        result.reason_code = "too_close"
        result.reason = (
            f"Too close: minimum distance is {weapon.min_distance:g} m"
        )
        return result

    g = weapon.g

    if g == 0:
        # No gravity: the projectile flies straight along the line of sight.
        v = weapon.velocity_at(math.hypot(distance, height_diff))
        rad = math.atan2(height_diff, distance)
        raw = {"low": rad, "high": rad}
    else:
        v = weapon.velocity_at(distance)

        discriminant = (
            v ** 4 - g * (g * distance ** 2 + 2 * height_diff * v ** 2)
        )

        if discriminant < 0:
            result.reason_code = "out_of_range"
            result.reason = (
                f"Out of range (max ~{weapon.max_range():.0f} m "
                "on flat ground)"
            )
            return result

        root = math.sqrt(discriminant)

        raw = {
            "low": math.atan((v ** 2 - root) / (g * distance)),
            "high": math.atan((v ** 2 + root) / (g * distance)),
        }

    result.velocity = v

    low_limit, high_limit = weapon.elevation_limits

    for name, rad in raw.items():
        angle = math.degrees(rad) - weapon.angle_offset
        if low_limit <= angle <= high_limit:
            result.alternatives[name] = angle

    rad = raw[arc]
    angle = math.degrees(rad) - weapon.angle_offset

    result.angle = angle
    result.raw_angle = math.degrees(rad)

    if not low_limit <= angle <= high_limit:
        result.reason_code = "elevation_limit"
        result.reason = (
            f"{arc.capitalize()} arc needs {angle:.1f}°, weapon elevation "
            f"is limited to {low_limit:g}°..{high_limit:g}°"
        )
        return result

    result.reachable = True
    result.mils = angle * MILS_PER_DEGREE
    result.time_of_flight = distance / (v * math.cos(rad))

    if g == 0:
        result.apex = max(0.0, height_diff)
        result.impact_angle = -math.degrees(rad)
    else:
        top_x = v * v * math.sin(rad) * math.cos(rad) / g
        top_x = min(max(top_x, 0.0), distance)
        result.apex = max(0.0, _path(v, g, rad, top_x), height_diff)

        slope = math.tan(rad) - g * distance / (v * v * math.cos(rad) ** 2)
        result.impact_angle = -math.degrees(math.atan(slope))

    return result


def trajectory(weapon, solution, points=64):
    """Sample the flight path of a solved shot as (x, y) tuples."""
    if not math.isfinite(solution.raw_angle):
        return []

    rad = math.radians(solution.raw_angle)
    v = solution.velocity
    g = weapon.g
    d = solution.distance

    return [
        (d * i / points, _path(v, g, rad, d * i / points))
        for i in range(points + 1)
    ]


def height_at(weapon, angle, distance):
    """Height of the projectile after travelling `distance` metres.

    `angle` is the elevation as returned by `solve` (angle_offset applied).
    Used for verification and tests.
    """
    rad = math.radians(angle + weapon.angle_offset)
    return _path(weapon.velocity_at(distance), weapon.g, rad, distance)


def screen_offset(angle, fov, screen_width, scale=1.0):
    """Vertical pixel offset of the aim point for a given elevation.

    Squad renders with a rectilinear projection and a horizontal FOV, so the
    focal length in pixels is (width / 2) / tan(fov / 2). A point that is
    `angle` degrees below the view centre is projected focal * tan(angle)
    pixels below it. Raising the barrel by `angle` therefore means placing
    the target that many pixels BELOW the screen centre.
    """
    if not 1 <= fov <= 179:
        raise ValueError("FOV must be between 1 and 179 degrees")
    if screen_width <= 0:
        raise ValueError("Screen width must be positive")

    if abs(angle) >= 89.9:
        return math.copysign(math.inf, angle)

    focal = (screen_width / 2) / math.tan(math.radians(fov) / 2)
    return focal * math.tan(math.radians(angle)) * scale


def load_weapons(path):
    """Load weapons.json into an ordered {name: Weapon} dict."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise WeaponDataError(f"Weapons file not found: {path}")
    except json.JSONDecodeError as e:
        raise WeaponDataError(f"weapons.json is not valid JSON: {e}")

    return parse_weapons(raw)


def parse_weapons(raw):
    if not isinstance(raw, dict):
        raise WeaponDataError("weapons.json must contain an object")

    weapons = {}
    for name, data in raw.items():
        # Keys starting with "_" are comments / metadata.
        if name.startswith("_"):
            continue
        weapons[name] = Weapon.from_dict(name, data)

    if not weapons:
        raise WeaponDataError("weapons.json does not define any weapons")

    return weapons
