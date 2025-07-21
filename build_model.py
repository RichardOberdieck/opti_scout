from classes import Timeslot , Activity, ScoutGroup, priority, AssigningActivititesProblem

import datetime, json

from utilities import readAndTranslateJsonActivityRefs




def generate_variables(model, groups):
   print("Generate variables")
   x = {}
   for g in groups:
      for p in g.priorities:
         activity = p.activity
         for s in activity.available_sessions:
            x[(g.identifier, activity.identifier, s.startname())] = model.add_var(var_type=BINARY, name=g.identifier+"_"+activity.identifier+"_start"+s.startname())
            print(x[(g.identifier, activity.identifier, s.startname())])
   print("Variable generated:", len(x))    
   print (x)     
   return x



#any session of an activity cannot have more than the max number of participants
def add_maxscout_constraint(m,groups,activities,x):
   for a in activities:
      for s in a.available_sessions:
         lhs=[]
         for g in groups:
            if g.hasActivity(a):
               lhs.append(g.size*x[(g.identifier, a.identifier, s.startname())])
         m += xsum(lhs) <= a.max_participants




#find all activities where age does not match and force these to zero
def add_age_constraint(m,groups,activities,x,unavail):
   for a in activities:
      for s in a.available_sessions:
         for g in groups:
            if g.hasActivity(a) and g.agegroup not in a.allowed_age_groups:
               name="group_"+g.identifier+"_does_not_have_age_required_for_"+a.identifier+"_"+s.startname()
               m += x[(g.identifier, a.identifier, s.startname())] <= 0, name   
               unavail.append((x[(g.identifier, a.identifier, s.startname())], name))
   return unavail



# one group gets at most one session from any activity
def add_max_1_session_constraint(m,groups,x):
   lhs=[]   
   for g in groups:
      for p in g.priorities:
         activity = p.activity
         lhs.clear()
         for s in activity.available_sessions:
            lhs.append(x[(g.identifier, activity.identifier, s.startname())])
         #only need to add constraint if there is more than one   
         if len(lhs) > 1:       
            name = "group_"+g.identifier+"_at_most_1_session_for_activity_"+activity.identifier
            m += xsum(lhs) <= 1, name
   

#Any group having an out-of-camp session can do nothing else this day, no other out-of-camp or in-camp activities (kind of hard constraint, but reasonable)
def add_outofcamp_activities_constraint(m,groups,activities,x):
   for g in groups:
      for p in g.priorities:
         a = p.activity
         if a.out_of_camp:
            #This will generate to many constraints if any other outofcamp activities are prioritiezed
            print(g.identifier,"has out of camp activity (any session selected should prevent any other activities on the same day):",a.identifier)
            #we could just loop through the remaining priorities as the previous ones has been checked
            for p1 in g.priorities:
               a1=p1.activity
               if a.identifier != a1.identifier:
                  for s in a.available_sessions:
                     #print("session:",a.identifier,s.startname())
                     for s1 in a1.available_sessions:
                        if s.sameday(s1):
                           #print("SAME DAY:",a1.identifier,s1.startname())
                           name = "group_"+g.identifier+"_out_of_camp_constraint_"+a.identifier+"_"+s.startname()+"_"+a1.identifier+"_"+s1.startname()
                           print(name) 
                           m += x[(g.identifier, a.identifier, s.startname())] + x[(g.identifier, a1.identifier, s1.startname())] <= 1, name  
   

# any group can at most  have 1 session of overlapping sessions across all activities that they have prioritized
def add_max_1_of_overlapping_sessions_constraint(m,groups,x):
   lhs = []
   for g in groups:
      for p in g.priorities:
         a = p.activity
         for s in a.available_sessions:
            lhs.clear()
            lhs.append(x[(g.identifier, a.identifier, s.startname())])
            for p1 in g.priorities:
               #check against all other priority sessions
               a1=p1.activity
               if a != a1:
                  for s1 in a1.available_sessions:
                     if s.overlaps(s1):
                        lhs.append(x[(g.identifier, a1.identifier, s1.startname())])
            if len(lhs) > 1 :            
               name = "group_"+g.identifier+"_can_only_attend_one_of_these_as_they_overlap_in_time_"+s.startname()            
               print(name,"nb of vars: ", len(lhs))
               m += xsum(lhs) <= 1, name

#If a session falls outside the groups available hours, then force it to 0
#This could be avoided if we only generated variables representing sessions in available timeslots for groups
def add_unavailable_time_constraint(m,groups,x):
   u=[]
   for g in groups:      
      #get all timeslots for one group
      for p in g.priorities:
         a = p.activity
         #loop over all available session for this priority
         for s in a.available_sessions:
            #group cannot attend session until we have found that this session is within the available times for the group
            if g.InAvailableTimeslots(s) == False:
               name = "groupDoesNotHaveAvailabletime_"+g.identifier+"_"+a.identifier+"_start"+s.startname()
               print ("False session InAvailableTimeslot genereate constraint: ",name)
               #store list of vars set to 0 as they are in unavailable times for the group
               u.append((x[(g.identifier, a.identifier, s.startname())],name))
               #create actual constraint
               m += x[(g.identifier, a.identifier, s.startname())] <= 0, name 
            else:
               print ("True session InAvailableTimeslot no consgtraint needed")    
   return u

#define the objective function
def add_objective(m,groups,x):
   lhs=[]   
   for g in groups:
      for p in g.priorities:
         activity = p.activity
         for s in activity.available_sessions:
            lhs.append(p.value*x[(g.identifier, activity.identifier, s.startname())])
   print("Define objective function using all vars included")
   m.objective = maximize(xsum(lhs))


#run the model optimization and report the solution
def optimizemodel(m, u):
   status = m.optimize(max_seconds=300)
   print(status)
   if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
      #print(u)
      print('solution:')
      for var in m.vars:
         # if this was set to zero for any reason and report as part of the solution
         for i in range(len(u)):
            if var.name == u[i][0].name:
               print("Next forced to zero as",u[i][1])
         print('{} : {}'.format(var.name, var.x))
  


 
   



from mip import *
model = Model()

translatedfile="C:\\Optimization\opti_scout\optiscout\\jsonreftranslated.json "
readAndTranslateJsonActivityRefs("C:\\Optimization\opti_scout\optiscout\\testdata_ref.json", translatedfile)

#read the model data
inputfile = open(translatedfile, "r")
assign_activity_problem = AssigningActivititesProblem(**json.load(inputfile))


x = generate_variables(model,assign_activity_problem.scoutgroups)

add_maxscout_constraint(model, assign_activity_problem.scoutgroups, assign_activity_problem.activities, x)
add_max_1_session_constraint(model,assign_activity_problem.scoutgroups,x)
add_max_1_of_overlapping_sessions_constraint(model,assign_activity_problem.scoutgroups,x)
unavailable = add_unavailable_time_constraint(model,assign_activity_problem.scoutgroups,x)
unavailable = add_age_constraint(model,assign_activity_problem.scoutgroups,assign_activity_problem.activities,x,unavailable)
add_outofcamp_activities_constraint(model,assign_activity_problem.scoutgroups,assign_activity_problem.activities,x)

add_objective(model,assign_activity_problem.scoutgroups,x)

optimizemodel(model, unavailable)

