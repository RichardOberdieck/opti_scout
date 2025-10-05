from hypothesis import given, settings, strategies as st
from datetime import datetime, timedelta

from opti_scout.build_model import ModelBuilder
from opti_scout.classes import Activity, ScoutGroup, Timeslot, Selection, AssigningActivititesProblem


def timeslots():
    base = datetime(2025, 9, 25, 8, 0)
    # Generate a list of non-overlapping timeslots by picking unique offsets
    offsets = list(range(0, 12, 2))  # e.g., 0, 2, 4, 6, 8, 10
    return [
        Timeslot(start=base + timedelta(hours=offset), end=base + timedelta(hours=offset + 1)) for offset in offsets
    ]


def allowed_age_groups():
    return [8, 12, 13, 14, 15]


@st.composite
def activity_strategy(draw):
    ts = draw(st.sets(st.sampled_from(timeslots()), min_size=3, max_size=7))
    return Activity(
        name=draw(st.text(min_size=3, max_size=10)),
        identifier=draw(st.text(min_size=1, max_size=3)),
        allowed_age_groups=set(allowed_age_groups()),
        max_participants=draw(st.integers(min_value=5, max_value=20)),
        available_sessions=ts,
        out_of_camp=draw(st.booleans()),
    )


@st.composite
def scoutgroup_strategy(draw):
    return ScoutGroup(
        name=draw(st.text(min_size=3, max_size=10)),
        identifier=draw(st.text(min_size=1, max_size=3)),
        agegroup=draw(st.sampled_from(allowed_age_groups())),
        size=draw(st.integers(min_value=5, max_value=20)),
        available_timeslots=draw(st.sets(st.sampled_from(timeslots()), min_size=1, max_size=3)),
    )


@st.composite
def assigning_activities_problem_strategy(draw):
    # Generate activities
    activities = draw(st.lists(activity_strategy(), min_size=1, max_size=2))

    # Generate scoutgroups
    scoutgroups = [
        draw(scoutgroup_strategy()),
        draw(scoutgroup_strategy()),
        draw(scoutgroup_strategy()),
        draw(scoutgroup_strategy()),
    ]
    # Generate selections
    selections = set()
    for sg in scoutgroups:
        for act in activities:
            for ts in act.available_sessions:
                selections.add(Selection(scout_group=sg, activity=act, time_slot=ts, priority=1))
    return AssigningActivititesProblem(activities=activities, scoutgroups=scoutgroups, selections=selections)


def test_generate_variables(assigning_activities_problem: AssigningActivititesProblem):
    # Arrange
    model_builder = ModelBuilder.create(assigning_activities_problem)

    # Act
    x = model_builder.generate_variables()

    # Assert
    assert 26 == len(x)


@given(problem=assigning_activities_problem_strategy())
@settings(deadline=None)
def test_age_limit_respected(problem: AssigningActivititesProblem):
    # Arrange
    model_builder = ModelBuilder.create(problem)

    # Act
    solution = model_builder.solve()

    # Assert
    if any(solution.selections):
        for selection in solution.selections:
            assert selection.scout_group.agegroup in selection.activity.allowed_age_groups
