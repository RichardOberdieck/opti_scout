from opti_scout.classes import AssigningActivititesProblem, Solution
from pydantic import BaseModel
from mip import BINARY, xsum, Model, maximize, Var
import os

class ModelBuilder(BaseModel, arbitrary_types_allowed=True):
   assigning_activities_problem: AssigningActivititesProblem
   model: Model

   @classmethod
   def create(cls, assigning_activities_problem: AssigningActivititesProblem) -> "ModelBuilder":
       return cls(assigning_activities_problem=assigning_activities_problem, model=Model())


   def solve(self) -> Solution:
      x = self.generate_variables()

      self.add_maxscout_constraint(x)
      self.add_max_1_session_constraint(x)
      self.add_max_1_of_overlapping_sessions_constraint(x)
      self.add_unavailable_time_constraint(x)
      self.add_onlyone_activitylocation_eachday_constraint(x)
      self.add_age_constraint(x)
      #number is the maxmimum of popular activities
      self.add_max_nb_of_most_popular_activities_constraint(x, 2)

      self.add_objective(x)

      status = self.model.optimize(max_seconds=300)
      return Solution.build(x, status)


   def generate_variables(self) -> dict[tuple, Var]:
      return {
         s: self.model.add_var(var_type=BINARY, name=str(s)) for s in self.assigning_activities_problem.selections
      }

   #any session of an activity cannot have more than the max number of participants for that session (capacity may  vary for each session of an activity)
   def add_maxscout_constraint(self, x: dict[tuple, Var]) -> None:
      print ("add_maxscout_constraint")
      for a in self.assigning_activities_problem.activities:
         for activity_session in a.timeslots:
               #print("one activity session")
               #print (a.id, activity_session.id)
               selections = {
                  s
                  for s in self.assigning_activities_problem.selections
                  if s.activity == a and s.time_slot == activity_session
               }
               self.model += xsum(s.group.size * x[s] for s in selections) <= activity_session.capacity
               #print (selections)
               
   # one group gets at most one session from any activity
   def add_max_1_session_constraint(self, x: dict[tuple, Var]) -> None:
      print("add_max_1_session_constraint")
      for g in self.assigning_activities_problem.groups:
         for a in self.assigning_activities_problem.activities:
            selections = [
               s for s in self.assigning_activities_problem.selections if s.group == g and s.activity == a
            ]
            #print (a.id, g.id)
            #print (selections)
            self.model += (
               xsum(x[s] for s in selections) <= 1,
               "group_" + g.id + "_at_most_1_session_for_activity_" + a.id,
            )

   # any group can at most have 1 session of overlapping sessions across all activities that they have prioritized
   def add_max_1_of_overlapping_sessions_constraint(self, x: dict[tuple, Var]) -> None:
      print("add_max_1_of_overlapping_sessions_constraint")
      for s in self.assigning_activities_problem.selections:
         for s1 in self.assigning_activities_problem.get_overlapping_selections(s):
            self.model += (
               x[s] + x[s1] <= 1,
               f"overlapping_sessions_{s}_and_{s1}_for_group_{s.group.id}",
            )


   # If a session falls outside the groups available hours, then force it to 0
   # This could be avoided if we only generated variables representing sessions in available timeslots for groups
   def add_unavailable_time_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
      print("add_unavailable_time_constraint")      
      for s in self.assigning_activities_problem.selections:
         if s.group.in_available_timeslots(s.time_slot):
               continue

         self.model += (
               x[s] <= 0,
               f"groupDoesNotHaveAvailabletime_{s.group.id}_{s.activity.id}_start{s.time_slot.startname()}",
         )


   # Any group can only do activities in same location
   # That is for each selection, make sure no other selections at other locations can take place
   # A lot of 2 seleciton constraints
   def add_onlyone_activitylocation_eachday_constraint(self, x: dict[tuple, Var]) -> None:
      print("add_onlyone_activitylocation_eachday_constraint")
      for s in self.assigning_activities_problem.selections:

         selections = self.assigning_activities_problem.get_all_selections_on_other_locations_for_different_activities_same_day(s)
         for s1 in selections:
               self.model += x[s] + x[s1] <= 1, f"{s}_and_{s1}_excluded_because_different_location_same_day_{s.activity}"



    # find all activities where age does not match and force these to zero
    #this should not happen for any, as data is supposed to be cleaned, keep it as a check
   def add_age_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
      print("add_age_constraint")
      for s in self.assigning_activities_problem.selections:
         if s.group.age_span.low >= s.activity.age_span.low and s.group.age_span.high <= s.activity.age_span.high :
               continue

         print(f"NOTE found selection where age group not with allowed ages {s.group.id} {s.activity.id}, this should not be the case, adding constraint to prevent assignment")
         self.model += (
               x[s] <= 0,
               f"group_{s.group.id}_does_not_have_age_required_for_{s.activity.id}_{s.time_slot.id}_{s.time_slot.startname()}",
         )

    # find most popular activities and constrain to max_activities
    # another constraint will make sure at the most one session for one activity
   def add_max_nb_of_most_popular_activities_constraint(self, x: dict[tuple, Var],max_activities: int) -> list[tuple]:
      print("add_max_nb_of_most_popular_activities_constraint")
      for g in self.assigning_activities_problem.groups:
         selections = [
               s for s in self.assigning_activities_problem.selections if s.group == g and s.activity in self.assigning_activities_problem.popularactivities
            ]
         #print (g.id)
         #print (selections)
         self.model += (
            xsum(x[s] for s in selections) <= max_activities,
            "group_" + g.id + "_at_most_1_popular_activity",
         )      


   # define the objective function
   def add_objective(self, x: dict[tuple, Var]) -> None:
      print("add objective")
      self.model.objective = maximize(xsum(s.priority * x[s] for s in self.assigning_activities_problem.selections))



   
