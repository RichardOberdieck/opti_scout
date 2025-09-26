from opti_scout.build_model import ModelBuilder
from pytest import fixture

from opti_scout.classes import AssigningActivititesProblem


@fixture
def model_builder(assigning_activities_problem: AssigningActivititesProblem) -> ModelBuilder:
    return ModelBuilder.create(assigning_activities_problem)


def test_generate_variables(model_builder: ModelBuilder):
    # Act
    x = model_builder.generate_variables()

    # Assert
    assert 26 == len(x)


def test_solve(model_builder: ModelBuilder):
    # Act
    model_builder.solve()
