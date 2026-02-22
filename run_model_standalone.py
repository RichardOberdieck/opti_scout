from opti_scout.classes import AssigningActivititesProblem
from opti_scout.build_model import ModelBuilder

import os


# change path to where ever the python file is
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
currpath = os.getcwd()
print("we are now in: ", currpath)
assign_activity_problem = AssigningActivititesProblem.from_json("../opti_scout/tests/data/tom_full_periodeid.json")

model_builder = ModelBuilder.create(assign_activity_problem)

popact = assign_activity_problem.get_popular_activities()
print("Most Popular activities")
for a in popact:
    print(a.id)


solution = model_builder.solve()

solution.to_excel("tomtest.xlsx")

# todo
# check uniqueness of ids for groups, activities, priorities
