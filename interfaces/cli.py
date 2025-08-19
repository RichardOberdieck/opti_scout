import click

from opti_scout.build_model import ModelBuilder
from opti_scout.classes import AssigningActivititesProblem


@click.command
@click.option("--input_file", help="json file with the input data")
@click.option("--output_file", default="results.json", help="json file with the results")
def run(input_file: str, output_file: str):
    assigning_activities_problem = AssigningActivititesProblem.from_json(input_file)
    model_builder = ModelBuilder.create(assigning_activities_problem)
    solution = model_builder.solve()
    if solution is not None:
        with open(output_file, "w") as file:
            file.write(solution.model_dump_json())


if __name__ == "__main__":
    run()
