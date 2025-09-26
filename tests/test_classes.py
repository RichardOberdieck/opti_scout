from opti_scout.classes import Activity, AssigningActivititesProblem, ScoutGroup, Selection, Timeslot

from datetime import datetime
from pytest import fixture, mark


@fixture
def timeslots():
    return [
        Timeslot(start=datetime(2025, 9, 25, 9, 0), end=datetime(2025, 9, 25, 10, 0)),
        Timeslot(start=datetime(2025, 9, 25, 9, 30), end=datetime(2025, 9, 25, 16, 0)),
    ]


@fixture
def assigning_activities_problem():
    return AssigningActivititesProblem.from_json("tests/data/testdata_ref.json")


@mark.parametrize(
    "slot1, slot2, expected",
    [
        # Identical timeslots
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            True,
        ),
        # slot2 starts during slot1
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 11)),
            Timeslot(start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 12)),
            True,
        ),
        # slot2 ends during slot1
        (
            Timeslot(start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 12)),
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 11)),
            True,
        ),
        # slot2 fully inside slot1
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 12)),
            Timeslot(start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 11)),
            True,
        ),
        # slot1 fully inside slot2
        (
            Timeslot(start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 11)),
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 12)),
            True,
        ),
        # Adjacent timeslots (no overlap)
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 11)),
            False,
        ),
        # Completely separate timeslots
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 25, 11), end=datetime(2025, 9, 25, 12)),
            False,
        ),
        # Overlap across midnight
        (
            Timeslot(start=datetime(2025, 9, 25, 23), end=datetime(2025, 9, 26, 1)),
            Timeslot(start=datetime(2025, 9, 26, 0), end=datetime(2025, 9, 26, 2)),
            True,
        ),
    ],
)
def test_timeslot_overlap(slot1, slot2, expected):
    assert slot1.overlaps(slot2) == expected
    assert slot2.overlaps(slot1) == expected  # symmetry check


@mark.parametrize(
    "slot1, slot2, expected",
    [
        # Is same day
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 25, 22), end=datetime(2025, 9, 25, 23)),
            True,
        ),
        # Is definitely not same day
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 23, 22), end=datetime(2025, 9, 23, 23)),
            False,
        ),
        # End time matches
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 24, 22), end=datetime(2025, 9, 25, 2)),
            True,
        ),
        # Start time matches
        (
            Timeslot(start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            Timeslot(start=datetime(2025, 9, 25, 22), end=datetime(2025, 9, 26, 2)),
            True,
        ),
    ],
)
def test_timeslot_is_same_day(slot1, slot2, expected):
    assert slot1.is_same_day(slot2) == expected
    assert slot2.is_same_day(slot1) == expected


def test_get_overlapping_selections(timeslots):
    # Create Activities
    activity1 = Activity(
        name="Archery",
        identifier="A1",
        allowed_age_groups={10, 11, 12},
        max_participants=20,
        available_sessions=set([timeslots[0]]),
        out_of_camp=False,
    )
    activity2 = Activity(
        name="Kayaking",
        identifier="A2",
        allowed_age_groups={12, 13, 14},
        max_participants=15,
        available_sessions=set([timeslots[1]]),
        out_of_camp=True,
    )

    # Create ScoutGroups
    group1 = ScoutGroup(name="Eagles", identifier="G1", agegroup=12, size=10, available_timeslots=set(timeslots))
    group2 = ScoutGroup(name="Wolves", identifier="G2", agegroup=13, size=8, available_timeslots=set([timeslots[1]]))

    # Create Selections
    selection1 = Selection(scout_group=group1, activity=activity1, time_slot=timeslots[0], priority=1)
    selection1a = Selection(scout_group=group1, activity=activity1, time_slot=timeslots[1], priority=1)
    selection2 = Selection(scout_group=group1, activity=activity2, time_slot=timeslots[1], priority=2)
    selection3 = Selection(scout_group=group2, activity=activity2, time_slot=timeslots[1], priority=1)

    # Act
    problem = AssigningActivititesProblem(
        activities=[activity1, activity2],
        scoutgroups=[group1, group2],
        selections=[selection1, selection2, selection3, selection1a],
    )

    overlapping_selections = problem.get_overlapping_selections(selection1)

    # Assert
    assert len(overlapping_selections) == 1
    assert (
        Selection(scout_group=group1, activity=activity2, time_slot=timeslots[1], priority=2)
        == overlapping_selections.pop()
    )
