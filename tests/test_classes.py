from opti_scout.classes import AssigningActivititesProblem
from pytest import fixture


@fixture
def assigning_activities_problem():
    return AssigningActivititesProblem.from_json("tests/data/testdata_ref.json")


def test_get_selections_for_activity(assigning_activities_problem: AssigningActivititesProblem):
    # Arrange
    pass