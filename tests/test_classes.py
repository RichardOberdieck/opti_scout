from opti_scout.classes import Activity, AssigningActivititesProblem, Group, Selection, Timeslot, ActivityTimeslot

from datetime import datetime
from pytest import fixture, mark


@fixture
def timeslots():
    return [
        Timeslot(start=datetime(2025, 9, 25, 9, 0), end=datetime(2025, 9, 25, 10, 0)),
        Timeslot(start=datetime(2025, 9, 25, 9, 30), end=datetime(2025, 9, 25, 16, 0)),
    ]


@fixture
def activitytimeslots():
    return [
        ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9, 0), end=datetime(2025, 9, 25, 10, 0)),
        ActivityTimeslot(
            id="p0002", capacity=100, start=datetime(2025, 9, 25, 9, 30), end=datetime(2025, 9, 25, 16, 0)
        ),
    ]


@fixture
def assigning_activities_problem():
    return AssigningActivititesProblem.from_json("tests/data/tom_full_periodeid.json")


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
    "slot3, slot4, expected",
    [
        # Identical timeslots
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            ActivityTimeslot(id="p0002", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            True,
        ),
        # slot3 starts during slot4
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 11)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 12)),
            True,
        ),
        # slot4 ends during slot3
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 12)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 11)),
            True,
        ),
        # slot4 fully inside slot3
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 12)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 11)),
            True,
        ),
        # slot3 fully inside slot4
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 11)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 12)),
            True,
        ),
        # Adjacent timeslots (no overlap)
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 10), end=datetime(2025, 9, 25, 11)),
            False,
        ),
        # Completely separate timeslots
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 9), end=datetime(2025, 9, 25, 10)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 11), end=datetime(2025, 9, 25, 12)),
            False,
        ),
        # Overlap across midnight
        (
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 25, 23), end=datetime(2025, 9, 26, 1)),
            ActivityTimeslot(id="p0001", capacity=300, start=datetime(2025, 9, 26, 0), end=datetime(2025, 9, 26, 2)),
            True,
        ),
    ],
)
def test_activitytimeslot_overlap(slot3, slot4, expected):
    assert slot3.overlaps(slot4) == expected
    assert slot4.overlaps(slot3) == expected  # symmetry check


def test_get_overlapping_selections(timeslots, activitytimeslots):
    # Create Activities
    activity1 = Activity(
        name="Archery",
        id="A0001",
        age_span={"low": 7, "high": 10},
        timeslots=set([activitytimeslots[0]]),
        activity_area="Lejren",
        in_camp=False,
    )
    activity2 = Activity(
        name="Kayaking",
        id="A0002",
        age_span={"low": 7, "high": 10},
        timeslots=set([activitytimeslots[1]]),
        activity_area="Lejren",
        in_camp=False,
    )

    # Create ScoutGroups
    group1 = Group(name="Eagles", id="G0001", age_span={"low": 7, "high": 10}, size=10, available=set(timeslots))
    group2 = Group(name="Wolves", id="G0002", age_span={"low": 7, "high": 10}, size=8, available=set([timeslots[1]]))

    # Create Selections
    selection1 = Selection(group=group1, activity=activity1, time_slot=activitytimeslots[0], priority=1)
    selection1a = Selection(group=group1, activity=activity1, time_slot=activitytimeslots[1], priority=1)
    selection2 = Selection(group=group1, activity=activity2, time_slot=activitytimeslots[1], priority=2)
    selection3 = Selection(group=group2, activity=activity2, time_slot=activitytimeslots[1], priority=1)

    # Act
    problem = AssigningActivititesProblem(
        activities=[activity1, activity2],
        groups=[group1, group2],
        selections=[selection1, selection2, selection3, selection1a],
        popularactivities=[activity1],
    )

    overlapping_selections = problem.get_overlapping_selections(selection1)

    # Assert
    assert len(overlapping_selections) == 1
    assert (
        Selection(group=group1, activity=activity2, time_slot=activitytimeslots[1], priority=2)
        == overlapping_selections.pop()
    )
