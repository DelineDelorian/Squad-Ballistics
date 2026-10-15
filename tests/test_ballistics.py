import math
import os

import pytest

from ballistics import (
    GRAVITY,
    MILS_PER_DEGREE,
    Weapon,
    WeaponDataError,
    height_at,
    load_weapons,
    parse_weapons,
    screen_offset,
    solve,
    trajectory,
)

from conftest import ROOT

WEAPONS = load_weapons(os.path.join(ROOT, "weapons.json"))


def test_database_loads():
    assert len(WEAPONS) >= 50

    # Weapons of the original release must still be covered.
    for name in (
        "MK19 / AGS-17 / AGS-30",
        "RPG-29",
        "SPG-9 · HEAT",
        "ZiS-3",
        "Rifle grenade",
        "M203 / M320 / GP-25 / HK79 / MKE MGL",
    ):
        assert name in WEAPONS

    # Original values are kept.
    assert WEAPONS["SPG-9 · HEAT"].gravity == 1.2
    assert WEAPONS["ZiS-3"].velocity == 700


def test_every_weapon_has_known_category():
    from i18n import STRINGS

    for weapon in WEAPONS.values():
        assert f"cat_{weapon.category}" in STRINGS, weapon.name


@pytest.mark.parametrize("name", list(WEAPONS))
@pytest.mark.parametrize("fraction", [0.05, 0.25, 0.5, 0.8])
@pytest.mark.parametrize("height", [-30.0, 0.0, 20.0])
def test_every_weapon_hits_target(name, fraction, height):
    weapon = WEAPONS[name]

    distance = max(
        weapon.min_distance + 1,
        min(weapon.max_range() * fraction, 2000)
    )

    for arc in ("low", "high"):
        solution = solve(weapon, distance, height, arc)

        if not solution.reachable:
            # Only acceptable reason: weapon elevation limits.
            assert "limited" in solution.reason or "range" in solution.reason
            continue

        assert math.isfinite(solution.angle)
        assert solution.time_of_flight > 0
        assert solution.mils == pytest.approx(
            solution.angle * MILS_PER_DEGREE
        )

        # The projectile fired at that angle must pass through the target.
        assert height_at(weapon, solution.angle, distance) == pytest.approx(
            height, abs=0.01
        )


@pytest.mark.parametrize("name", list(WEAPONS))
def test_default_arc_reachable_somewhere(name):
    weapon = WEAPONS[name]

    for fraction in (0.3, 0.6, 0.85):
        distance = max(
            weapon.min_distance + 1,
            min(weapon.max_range() * fraction, 2000)
        )
        if solve(weapon, distance).reachable:
            return

    pytest.fail(f"{name} is never reachable with its default arc")


def test_gravity_scale_is_used():
    normal = Weapon("a", velocity=400, gravity=1)
    heavy = Weapon("b", velocity=400, gravity=2)

    a = solve(normal, 1000).angle
    b = solve(heavy, 1000).angle

    assert b > a * 1.9


def test_known_value():
    # Flat ground, no drag: sin(2θ) = g·d / v²
    weapon = Weapon("test", velocity=100)
    solution = solve(weapon, 500)

    expected = math.degrees(math.asin(GRAVITY * 500 / 100 ** 2) / 2)

    assert solution.angle == pytest.approx(expected)


def test_high_arc_is_higher():
    weapon = WEAPONS["Mortar (M252 / 2B14 / L16 / Type 63)"]

    solution = solve(weapon, 800)

    assert solution.arc == "high"
    assert solution.angle > 45
    assert solve(weapon, 800, arc="low").reachable is False


def test_out_of_range():
    weapon = WEAPONS["M203 / M320 / GP-25 / HK79 / MKE MGL"]

    solution = solve(weapon, weapon.max_range() + 50)

    assert not solution.reachable
    assert "range" in solution.reason


def test_min_distance():
    weapon = WEAPONS["Mortar (M252 / 2B14 / L16 / Type 63)"]

    solution = solve(weapon, 20)

    assert not solution.reachable
    assert "close" in solution.reason.lower()


def test_target_above_needs_more_elevation():
    weapon = WEAPONS["SPG-9 · HEAT"]

    assert solve(weapon, 600, 30).angle > solve(weapon, 600, 0).angle
    assert solve(weapon, 600, -30).angle < solve(weapon, 600, 0).angle


@pytest.mark.parametrize("distance", [0, -10, float("nan")])
def test_invalid_distance(distance):
    with pytest.raises(ValueError):
        solve(WEAPONS["SPG-9 · HEAT"], distance)


def test_deceleration_velocity():
    weapon = WEAPONS["UB-32 (S-5 rockets)"]

    assert weapon.velocity_at(1) == pytest.approx(300, abs=0.5)
    assert weapon.velocity_at(5000) < 300
    assert weapon.velocity_at(5000) > weapon.cruise_velocity


def test_angle_offset_applied():
    weapon = WEAPONS["Technical Mortar"]
    plain = Weapon("plain", velocity=110, arc="high")

    assert solve(weapon, 600).angle == pytest.approx(
        solve(plain, 600).angle - 5
    )


def test_screen_offset_projection():
    # 90° horizontal FOV on a 1920 px wide screen: focal length = 960 px.
    assert screen_offset(45, 90, 1920) == pytest.approx(960)
    assert screen_offset(0, 90, 1920) == 0
    assert screen_offset(-10, 90, 1920) < 0

    # Narrower FOV (zoom) means more pixels per degree.
    assert screen_offset(2, 40, 1920) > screen_offset(2, 90, 1920)

    assert screen_offset(2, 90, 1920, scale=1.5) == pytest.approx(
        screen_offset(2, 90, 1920) * 1.5
    )

    assert math.isinf(screen_offset(90, 90, 1920))


@pytest.mark.parametrize("fov", [0, 180, -5])
def test_screen_offset_invalid_fov(fov):
    with pytest.raises(ValueError):
        screen_offset(1, fov, 1920)


@pytest.mark.parametrize("data", [
    {"x": {}},
    {"x": {"velocity": 0}},
    {"x": {"velocity": "fast"}},
    {"x": {"velocity": 100, "gravity": -1}},
    {"x": {"velocity": 100, "aim": "telepathy"}},
    {"x": {"velocity": True}},
    {"x": {"velocity": 100, "arc": "sideways"}},
    {"x": {"velocity": 100, "elevation_limits": [10, 5]}},
    {"x": {"velocity": 100, "deceleration": 100, "deceleration_time": 1}},
    {"_comment": "only comments"},
    [],
])
def test_invalid_weapon_data(data):
    with pytest.raises(WeaponDataError):
        parse_weapons(data)


def test_legacy_format_still_works():
    weapons = parse_weapons({"Old": {"velocity": 230, "gravity": 1}})

    assert weapons["Old"].arc == "low"
    assert solve(weapons["Old"], 300).reachable


def test_rocket_boost_speeds_up():
    weapon = WEAPONS["RPG-7 · PG-7V HEAT / OG-7V"]

    assert weapon.velocity_at(1) == pytest.approx(117, abs=1)
    assert weapon.velocity_at(300) > 117
    assert weapon.velocity_at(5000) < weapon.cruise_velocity
    assert weapon.cruise_velocity == pytest.approx(117 + 187.5 * 0.8)

    # Boosted rocket needs less elevation than one without the motor.
    plain = Weapon("plain", velocity=117)
    assert solve(weapon, 300).angle < solve(plain, 300).angle


def test_boost_max_range_matches_reachability():
    weapon = WEAPONS["Carl Gustav / M3 MAAWS · HEAT"]
    limit = weapon.max_range()

    assert solve(weapon, limit * 0.99).reachable
    assert not solve(weapon, limit * 1.01).reachable


def test_no_gravity_flies_straight():
    weapon = WEAPONS["NLAW"]

    assert weapon.max_range() == math.inf
    assert solve(weapon, 400).angle == pytest.approx(0)
    assert solve(weapon, 400, 40).angle == pytest.approx(
        math.degrees(math.atan2(40, 400))
    )


@pytest.mark.parametrize("name", list(WEAPONS))
def test_trajectory_ends_on_target(name):
    weapon = WEAPONS[name]

    for fraction in (0.3, 0.6, 0.85):
        distance = max(
            weapon.min_distance + 1,
            min(weapon.max_range() * fraction, 2000)
        )
        solution = solve(weapon, distance, 5)
        if solution.reachable:
            break
    else:
        pytest.skip("not reachable 5 m above")

    path = trajectory(weapon, solution)

    assert path[0] == (0.0, 0.0)
    assert path[-1][0] == pytest.approx(distance)
    assert path[-1][1] == pytest.approx(5, abs=0.01)
    assert solution.apex >= 5 - 1e-6
    assert max(y for _, y in path) <= solution.apex + 1e-6


def test_impact_angle_and_apex():
    weapon = Weapon("flat", velocity=100)
    solution = solve(weapon, 500)

    # Symmetric parabola on flat ground: lands at the launch angle.
    assert solution.impact_angle == pytest.approx(solution.angle)
    assert solution.apex == pytest.approx(
        (100 * math.sin(math.radians(solution.angle))) ** 2 / (2 * GRAVITY)
    )


def test_reason_codes():
    mortar = WEAPONS["Mortar (M252 / 2B14 / L16 / Type 63)"]

    assert solve(mortar, 10).reason_code == "too_close"
    assert solve(mortar, 5000).reason_code == "out_of_range"
    assert solve(mortar, 800, arc="low").reason_code == "elevation_limit"
