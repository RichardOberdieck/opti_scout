import json

from pydantic import BaseModel
from classes import Activity, ScoutGroup, Parameters

# working_directory = os.getcwd()
# print(working_directory)

# C:\\Optimization\opti_test-main\tests\test_cases\small_output.json
# C:\\Optimization\opti_test-main\opti_test\optitest\tests\


class AssigningActivititesProblem(BaseModel):
    activities: list[Activity]
    scoutgroups: list[ScoutGroup]
    parameters: Parameters


inputfile = open("C:\\Optimization\opti_scout\optiscout\\testdata.json", "r")

assign_activity_problem = AssigningActivititesProblem(**json.load(inputfile))

# print(assign_activity_problem)

print("List of activities")
print(assign_activity_problem.activities)

print("List of scoutsgroupss")
print(assign_activity_problem.scoutgroups)
