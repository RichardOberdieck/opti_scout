from opti_scout.classes import AssigningActivititesProblem, Solution
from opti_scout.build_model import ModelBuilder

from pydantic import BaseModel
from mip import BINARY, xsum, Model, maximize, Var
import os


#change path to where ever the python file is
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
currpath=os.getcwd()
print ("we are now in: ",currpath)
#filename="20260218response_small"
filename="20260218response"
optionalSuffix="max10"
modelrunsecs=1200
maxsessions=10
minsessions=1
maxpopular=2 
assign_activity_problem =  AssigningActivititesProblem.from_json("../opti_scout/tests/data/"+filename+".json")

assign_activity_problem.write_base_info('../opti_scout/tests/output/')

resultname="../opti_scout/tests/output/"+filename+optionalSuffix+".xlsx"
resultname_all="../opti_scout/tests/output/"+filename+optionalSuffix+"_all.xlsx"
resultname_prop="../opti_scout/tests/output/"+filename+optionalSuffix+"_properties.xlsx"

model_builder = ModelBuilder.create(assign_activity_problem)

  

popact = assign_activity_problem.get_popular_activities()
print ("Most Popular activities")
for a in popact:
    print (a.id)

model_builder.maxSessionsPerGroup = maxsessions
model_builder.maxSolveSeconds=modelrunsecs
model_builder.maxPopularActivities=maxpopular

solution = model_builder.solve( filename="../opti_scout/tests/modelfiles/"+filename)


print("Input filename:" +filename)

solution.to_excel(resultname)
solution.to_visualization_excel(resultname_all)
#add model properties to solution excel workbook
model_builder.to_excel(resultname,mode="a",sheet="properties")
model_builder.to_excel(resultname_all,mode="a",sheet="properties")

#todo
# check uniqueness of ids for groups, activities, priorities

