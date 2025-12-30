from opti_scout.classes import Activity, AssigningActivititesProblem, Group, Selection, Timeslot, ActivityTimeslot
from opti_scout.build_model import ModelBuilder

from hypothesis import strategies as st
from datetime import datetime, timedelta


def allowed_age_groups():
    return [{"low": 7,"high": 10},{"low": 11,"high": 13},{"low": 10,"high": 99}]



def timeslots():
    base = datetime(2025, 9, 25, 8, 0)
    # Generate a list of non-overlapping timeslots by picking unique offsets
    offsets = list(range(0, 12, 2))  # e.g., 0, 2, 4, 6, 8, 10
    return [
        Timeslot(start=base + timedelta(hours=offset), end=base + timedelta(hours=offset + 1)) for offset in offsets
    ]


def timeslots():
    base = datetime(2025, 9, 25, 8, 0)
    # Generate a list of non-overlapping timeslots by picking unique offsets
    offsets = list(range(0, 12, 2))  # e.g., 0, 2, 4, 6, 8, 10
    return [
          Timeslot(start=base + timedelta(hours=offset), end=base + timedelta(hours=offset + 1)) for offset in offsets
    ]

def activitytimeslots():
    base = datetime(2025, 9, 25, 8, 0)
    # Generate a list of non-overlapping timeslots by picking unique offsets
    offsets = list(0, 12, 2)  # e.g., 0, 2, 4, 6, 8, 10
    ids = list("a0001","a0002","a0003") 
    return [
        ActivityTimeslot(id=ids[i],capacity=100,start=base + timedelta(hours=offset[i]), end=base + timedelta(hours=offset[i] + 1)) for i in range(0,3)
    ]


@st.composite
def activity_strategy(draw):
    ts = draw(st.sets(st.sampled_from(activitytimeslots()), min_size=3, max_size=7))
    return Activity(
        name=draw(st.text(min_size=3, max_size=10)),
        id=draw(st.text(min_size=1, max_size=3)),
        age_span={"low": 7,"high": 10},
        available_sessions=ts,
        activity_area = "Lejren",
        in_camp=draw(st.booleans()),
    )



@st.composite
def scoutgroup_strategy(draw):
    return Group(
        id(st.text(min_size=1, max_size=3)),
        age_span={"low": 7,"high": 10},
        size=draw(st.integers(min_value=5, max_value=20)),
        available=draw(st.sets(st.sampled_from(timeslots()), min_size=1, max_size=3)),
    )


@st.composite
def assigning_activities_problem_strategy(draw):
    # Generate activities
    activities = draw(st.lists(activity_strategy(), min_size=1, max_size=2))

    # Generate popular activities
    popactivities = activities[0]
    

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
            for ts in act.available:
                selections.add(Selection(group=sg, activity=act, time_slot=ts, priority=1))
    return AssigningActivititesProblem(activities=activities, groups=scoutgroups, selections=selections,popularactivities=popactivities)


def test_generate_variables(assigning_activities_problem: AssigningActivititesProblem):
    # Arrange
    model_builder = ModelBuilder.create(assigning_activities_problem)

    # Act
    x = model_builder.generate_variables()

    # Assert
    assert 12 == len(x)

