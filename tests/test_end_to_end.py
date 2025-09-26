from opti_scout.build_model import ModelBuilder
from opti_scout.classes import AssigningActivititesProblem


def test_end_to_end():
    assigning_activities_problem = AssigningActivititesProblem.from_json("tests/data/testdata_ref.json")
    model_builder = ModelBuilder.create(assigning_activities_problem)
    solution = model_builder.solve()

    assert solution is not None
    assert len(solution.assignments) == 4