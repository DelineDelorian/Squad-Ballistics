"""Ballistic math for Squad Ballistics.

Pure functions only (no Qt), so everything here can be unit-tested.

The projectile model matches the one used by SquadCalc: no air drag, a
per-weapon gravity scale and an optional constant-deceleration phase right
after launch (UB-32 rockets).
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


class WeaponDataError(ValueError):
    """Raised when weapons.json contains invalid data."""


@dataclass(frozen=True)
class Weapon:
    name: str
    velocity: float
    gravity: float = 1.0
    arc: str = "low"
    unit: str = "deg"
    angle_offset: float = 0.0
    deceleration: float = 0.0
    deceleration_time: float = 0.0
    min_distance: float = 0.0
    elevation_limits: tuple = (-90.0, 90.0)
    category: str = "Other"
    note: str = ""

    @classmethod
    def from_dict(cls, name, data):
        if not isinstance(data, dict):
            raise WeaponDataError(f"{name}: entry must be an object")

        try:
            velocity = float(data["velocity"])
        except KeyError:
            raise WeaponDataError(f"{name}: 'velocity' is required")
        except (TypeError, ValueError):
            raise WeaponDataError(f"{name}: 'velocity' must be a number")

        def number(key, default):
            value = data.get(key, default)
            try:
                return float(value)
            except (TypeError, ValueError):
                raise WeaponDataError(f"{name}: '{key}' must be a number")

        gravity = number("gravity", 1.0)
        deceleration = number("deceleration", 0.0)
        deceleration_time = number("deceleration_time", 0.0)

        if velocity <= 0:
            raise WeaponDataError(f"{name}: 'velocity' must be > 0")
        if gravity <= 0:
            raise WeaponDataError(f"{name}: 'gravity' must be > 0")
        if deceleration < 0 or deceleration_time < 0:
            raise WeaponDataError(f"{name}: deceleration values must be >= 0")
        if deceleration * deceleration_time >= velocity:
            raise WeaponDataError(
                f"{name}: deceleration would stop the projectile"
            )

        arc = data.get("arc", "low")
        if arc not in ARCS:
            raise WeaponDataError(f"{name}: 'arc' must be one of {ARCS}")

        unit = data.get("unit", "deg")
        if unit not in UNITS:
            raise WeaponDataError(f"{name}: 'unit' must be one of {UNITS}")

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
            angle_offset=number("angle_offset", 0.0),
            deceleration=deceleration,
            deceleration_time=deceleration_time,
            min_distance=number("min_distance", 0.0),
            elevation_limits=(low, high),
            category=str(data.get("category", "Other")),
            note=str(data.get("note", "")),
        )

    @property
    def g(self):
        return GRAVITY * self.gravity

    @property
    def deceleration_distance(self):
        t = self.deceleration_time
        return self.velocity * t - 0.5 * self.deceleration * t * t

    @property
    def cruise_velocity(self):
        return self.velocity - self.deceleration * self.deceleration_time

    def velocity_at(self, distance):
        """Average horizontal-equivalent velocity over `distance`.

        Same approximation as SquadCalc: during the deceleration phase the
        projectile slows down linearly, afterwards it cruises.
        """
        if self.deceleration <= 0 or self.deceleration_time <= 0:
            return self.velocity

        if distance <= 0:
            return self.velocity

        if distance <= self.deceleration_distance:
            t = (
                -self.velocity
                + math.sqrt(
                    self.velocity ** 2 + 2 * self.deceleration * distance
                )
            ) / self.deceleration
            return self.velocity - self.deceleration * t

        after = distance - self.deceleration_distance
        total_time = self.deceleration_time + after / self.cruise_velocity
        return distance / total_time

    def max_range(self):
        """Maximum range on flat ground (45 degrees)."""
        if self.deceleration <= 0 or self.deceleration_time <= 0:
            return self.velocity ** 2 / self.g

        lost = self.velocity - self.cruise_velocity
        return lost * self.deceleration_time + self.cruise_velocity ** 2 / self.g


@dataclass
class Solution:
    reachable: bool
    arc: str
    distance: float
    height_diff: float
    angle: float = math.nan          # elevation in degrees, angle_offset applied
    mils: float = math.nan
    time_of_flight: float = math.nan
    velocity: float = math.nan
    reason: str = ""
    alternatives: dict = field(default_factory=dict)


def resolve_arc(weapon, arc):
    if arc in (None, "", "auto"):
        return weapon.arc
    if arc not in ARCS:
        raise ValueError(f"Unknown arc '{arc}'")
    return arc


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
        result.reason = (
            f"Too close: minimum distance is {weapon.min_distance:g} m"
        )
        return result

    v = weapon.velocity_at(distance)
    g = weapon.g
    result.velocity = v

    discriminant = v ** 4 - g * (g * distance ** 2 + 2 * height_diff * v ** 2)

    if discriminant < 0:
        result.reason = (
            f"Out of range (max ~{weapon.max_range():.0f} m on flat ground)"
        )
        return result

    root = math.sqrt(discriminant)

    raw = {
        "low": math.atan((v ** 2 - root) / (g * distance)),
        "high": math.atan((v ** 2 + root) / (g * distance)),
    }

    low_limit, high_limit = weapon.elevation_limits

    for name, rad in raw.items():
        angle = math.degrees(rad) - weapon.angle_offset
        if low_limit <= angle <= high_limit:
            result.alternatives[name] = angle

    angle = math.degrees(raw[arc]) - weapon.angle_offset

    if not low_limit <= angle <= high_limit:
        result.angle = angle
        result.reason = (
            f"{arc.capitalize()} arc needs {angle:.1f}°, weapon elevation "
            f"is limited to {low_limit:g}°..{high_limit:g}°"
        )
        return result

    result.reachable = True
    result.angle = angle
    result.mils = angle * MILS_PER_DEGREE
    result.time_of_flight = distance / (v * math.cos(raw[arc]))
    return result


def height_at(weapon, angle, distance):
    """Height of the projectile after travelling `distance` metres.

    `angle` is the elevation as returned by `solve` (angle_offset applied).
    Used for verification and tests.
    """
    rad = math.radians(angle + weapon.angle_offset)
    v = weapon.velocity_at(distance)
    return (
        distance * math.tan(rad)
        - weapon.g * distance ** 2 / (2 * v ** 2 * math.cos(rad) ** 2)
    )


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
