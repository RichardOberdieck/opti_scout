from opti_scout.classes import AssigningActivititesProblem, Solution
from pydantic import BaseModel
from mip import BINARY, xsum, Model, maximize, Var
import time
import datetime
import pandas as pd


class ModelBuilder(BaseModel, arbitrary_types_allowed=True):
    assigning_activities_problem: AssigningActivititesProblem
    model: Model
    maxSessionsPerGroup: int
    maxSolveSeconds: int
    maxPopularActivities: int
    minSessionsPerGroup: int



    @classmethod
    def create(cls, assigning_activities_problem: AssigningActivititesProblem) -> "ModelBuilder":
        return cls(assigning_activities_problem=assigning_activities_problem, 
                   model=Model(),
                   maxSessionsPerGroup=100,
                   maxSolveSeconds=300,
                   maxPopularActivities=10,
                   minSessionsPerGroup=0)

    def solve(self, filename: str) -> Solution:

        x = self.generate_variables()

        print("Time:" + datetime.datetime.now().strftime("%H:%M:%S"))
        print("filename: " + filename)
        print("#Activities: " + str(len(self.assigning_activities_problem.activities)))
        print("#Activities without sessions: " + str(self.assigning_activities_problem.activitieswithoutsesessions))
        print("#Sessions: " + str(self.assigning_activities_problem.count_sessions()))
        print("#Groups: " + str(len(self.assigning_activities_problem.groups)))
        print("#Groups without priorities: " + str(self.assigning_activities_problem.grpswithoutselections))
        print("#selections: " + str(len(self.assigning_activities_problem.selections)))
        time.sleep(5)
        nbsteps=11
        actualstep=1
        starttime = datetime.datetime.now()
        print("add_maxscout_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_maxscout_constraint(x)
        addmax_scout_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_max_1_session_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_max_1_session_constraint(x)
        addmax_1_session_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_no_overlapping_sessions_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_no_overlapping_sessions_constraint(x)
        add_no_overlapping_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_unavailable_time_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        print("DISABLED as selections are only at valid times")
        #self.add_unavailable_time_constraint(x)
        add_unavailable_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_onlyone_activitylocation_eachday_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        print("DISABLED as we have the max one out of camp")
        #self.add_onlyone_activitylocation_eachday_constraint(x)
        add_location_eachday_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_age_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_age_constraint(x)
        add_age_time = datetime.datetime.now()
        # number is the maxmimum of popular activities
        actualstep=actualstep+1
        print("add_max_nb_of_most_popular_activities_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_max_nb_of_most_popular_activities_constraint(x)
        add_max_popular_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_min_1_session_per_group_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_min_session_per_group_constraint(x)
        add_min_1_session_per_group_time = datetime.datetime.now()
        actualstep=actualstep+1      
        print("add_max_sessions_per_group_constraint ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_max_sessions_per_group_constraint(x)
        add_max_sessions_per_group_constraint_time = datetime.datetime.now()
        actualstep=actualstep+1
        print("add_at_most_1_activity_out_of_camp ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_at_most_1_activity_out_of_camp(x)
        add_at_most_1_activity_out_of_camp_time= datetime.datetime.now()
        actualstep=actualstep+1
        print("add_objective ("+str(actualstep)+"/"+str(nbsteps)+")")
        self.add_objective(x)
        add_objective_time = datetime.datetime.now()
        modelready_time = datetime.datetime.now()

        print("filename: " + filename)
        print("#Activities: " + str(len(self.assigning_activities_problem.activities)))
        print("#Sessions: " + str(self.assigning_activities_problem.count_sessions()))

        print("#Groups: " + str(len(self.assigning_activities_problem.groups)))
        print("#selections: " + str(len(self.assigning_activities_problem.selections)))

        print("starttime:" + starttime.strftime("%H:%M:%S"))
        print("modelready_time:" + modelready_time.strftime("%H:%M:%S"))
        print("endtime starttime diff:" + str(int((modelready_time - starttime).total_seconds() // 60)) + " minutes")

        print(
            "addmax_scout_time: "
            + addmax_scout_time.strftime("%H:%M:%S")
            + "("
            + str(int((addmax_scout_time - starttime).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "addmax_1_session_time: "
            + addmax_1_session_time.strftime("%H:%M:%S")
            + "("
            + str(int((addmax_1_session_time - addmax_scout_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_no_overlapping_time: "
            + add_no_overlapping_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_no_overlapping_time - addmax_scout_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_unavailable_time: "
            + add_unavailable_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_unavailable_time - add_no_overlapping_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_1_location_eachday_time: "
            + add_location_eachday_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_location_eachday_time - add_unavailable_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_age_time: "
            + add_age_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_age_time - add_location_eachday_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_max_popular_time: "
            + add_max_popular_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_max_popular_time - add_age_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_min_1_session_per_group_time: "
            + add_min_1_session_per_group_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_min_1_session_per_group_time - add_max_popular_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_max_sessions_per_group_constraint_time: "
            + add_max_sessions_per_group_constraint_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_max_sessions_per_group_constraint_time - add_min_1_session_per_group_time ).total_seconds() // 60))
            + " minutes)"
        )
        
        print(
            "add_at_most_1_activity_out_of_camp_time: "
            + add_at_most_1_activity_out_of_camp_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_at_most_1_activity_out_of_camp_time - add_max_sessions_per_group_constraint_time).total_seconds() // 60))
            + " minutes)"
        )
        
        print(
            "add_objective_time: "
            + add_objective_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_objective_time - add_at_most_1_activity_out_of_camp_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "modelready_time: "
            + modelready_time.strftime("%H:%M:%S")
            + "("
            + str(int((modelready_time - add_objective_time).total_seconds() // 60))
            + " minutes)"
        )

        print(
            "modelready_time total: "
            + modelready_time.strftime("%H:%M:%S")
            + "("
            + str(int((modelready_time - starttime).total_seconds() // 60))
            + " minutes)"
        )

        modelfilename =filename + ".mps"
        print("Writing model to: " + modelfilename )
        self.model.write(modelfilename)
        
        print("Time:" + datetime.datetime.now().strftime("%H:%M:%S"))
        

        print("preproces")
        print(self.model.preprocess)
        # print("set preproces to 0")
        # self.model.preprocess=0

        status = self.model.optimize(max_seconds=self.maxSolveSeconds)
        endtime = datetime.datetime.now()

        print("#Activities: " + str(len(self.assigning_activities_problem.activities)))
        print("#Activities without sessions: " + str(self.assigning_activities_problem.activitieswithoutsesessions))
        print("#Sessions: " + str(self.assigning_activities_problem.count_sessions()))
        print("#Groups: " + str(len(self.assigning_activities_problem.groups)))
        print("#Groups without priorities: " + str(self.assigning_activities_problem.grpswithoutselections))
        print("#selections: " + str(len(self.assigning_activities_problem.selections)))

        print("starttime:" + starttime.strftime("%H:%M:%S"))
        print("endtime:" + endtime.strftime("%H:%M:%S"))
        print("endtime starttime diff:" + str(int((endtime - starttime).total_seconds() // 60)) + " minutes")

        print(
            "addmax_scout_time: "
            + addmax_scout_time.strftime("%H:%M:%S")
            + "("
            + str(int((addmax_scout_time - starttime).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "addmax_1_session_time: "
            + addmax_1_session_time.strftime("%H:%M:%S")
            + "("
            + str(int((addmax_1_session_time - addmax_scout_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_no_overlapping_time: "
            + add_no_overlapping_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_no_overlapping_time - addmax_scout_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_unavailable_time: "
            + add_unavailable_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_unavailable_time - add_no_overlapping_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_1_location_eachday_time: "
            + add_location_eachday_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_location_eachday_time - add_unavailable_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_age_time: "
            + add_age_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_age_time - add_location_eachday_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_max_popular_time: "
            + add_max_popular_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_max_popular_time - add_age_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_min_1_session_per_group_time: "
            + add_min_1_session_per_group_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_min_1_session_per_group_time - add_max_popular_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "add_max_sessions_per_group_constraint_time: "
            + add_max_sessions_per_group_constraint_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_max_sessions_per_group_constraint_time - add_min_1_session_per_group_time ).total_seconds() // 60))
            + " minutes)"
        )        
        print(
            "add_at_most_1_activity_out_of_camp_time: "
            + add_at_most_1_activity_out_of_camp_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_at_most_1_activity_out_of_camp_time - add_max_sessions_per_group_constraint_time).total_seconds() // 60))
            + " minutes)"
        )
        
        print(
            "add_objective_time: "
            + add_objective_time.strftime("%H:%M:%S")
            + "("
            + str(int((add_objective_time - add_at_most_1_activity_out_of_camp_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "modelready_time: "
            + modelready_time.strftime("%H:%M:%S")
            + "("
            + str(int((modelready_time - add_objective_time).total_seconds() // 60))
            + " minutes)"
        )
        print(
            "modelsolved_time: "
            + endtime.strftime("%H:%M:%S")
            + "("
            + str(int((endtime - modelready_time).total_seconds() // 60))
            + " minutes)"
        )

        return Solution.build(x, status)

    def generate_variables(self) -> dict[tuple, Var]:
        return {
            s: self.model.add_var(var_type=BINARY, name=str(s)) for s in self.assigning_activities_problem.selections
        }

    # any session of an activity cannot have more than the max number of participants for that session (capacity may  vary for each session of an activity)
    def add_maxscout_constraint(self, x: dict[tuple, Var]) -> None:
        print("add_maxscout_constraint")
        activitycounter = 0
        for a in self.assigning_activities_problem.activities:
            activitycounter = activitycounter + 1
            if activitycounter % 10 == 0:
                print(a.id)
            for activity_session in a.timeslots:
                # print("one activity session")
                # print (a.id, activity_session.id)
                selections = {
                    s
                    for s in self.assigning_activities_problem.selections
                    if s.activity == a and s.time_slot == activity_session
                }
                #if leaders can participate use the groupsize, otherwise use size without leaders 
                if a.leaders_can_participate == True:
                    self.model += xsum(s.group.size * x[s] for s in selections) <= activity_session.capacity
                else:    
                    self.model += xsum(s.group.size_without_leaders * x[s] for s in selections) <= activity_session.capacity
                # print (selections)

    # one group gets at most one session from any activity
    def add_max_1_session_constraint(self, x: dict[tuple, Var]) -> None:
        print("add_max_1_session_for_each_activity_constraint")
        grpcounter = 0
        for g in self.assigning_activities_problem.groups:
            grpcounter = grpcounter + 1
            if grpcounter % 25 == 0:
                print(g.id)
            for a in self.assigning_activities_problem.activities:
                selections = [
                    s for s in self.assigning_activities_problem.selections if s.group == g and s.activity == a
                ]
                # print (a.id, g.id)
                # print (selections)
                self.model += (
                    xsum(x[s] for s in selections) <= 1,
                    "group_" + g.id + "_at_most_1_session_for_activity_" + a.id,
                )

    # any group can at most have 1 session of overlapping sessions across all activities that they have prioritized
    def add_no_overlapping_sessions_constraint(self, x: dict[tuple, Var]) -> None:
        print("add_no_overlapping_sessions_constraint")
        sessioncounter = 0
        for s in self.assigning_activities_problem.selections:
            sessioncounter = sessioncounter + 1
            if sessioncounter % 1000 == 0:
                print(sessioncounter)
            for s1 in self.assigning_activities_problem.get_overlapping_selections(s):
                self.model += (
                    x[s] + x[s1] <= 1,
                    f"exclude_overlapping_sessions_for_{s.group.id}_{s.activity.id}_{s.time_slot.id}_with_{s1}",
                )

    # If a session falls outside the groups available hours, then force it to 0
    # This could be avoided if we only generated variables representing sessions in available timeslots for groups
    def add_unavailable_time_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
        print("add_unavailable_time_constraint")
        sessioncounter = 0
        for s in self.assigning_activities_problem.selections:
            sessioncounter = sessioncounter + 1
            if sessioncounter % 1000 == 0:
                print(sessioncounter)
            if s.group.in_available_timeslots(s.time_slot):
                continue

            self.model += (
                x[s] <= 0,
                f"groupDoesNotHaveAvailabletime_{s.group.id}_{s.activity.id}_{s.time_slot.id}",
            )

    # Any group can only do activities in same location
    # That is for each selection, make sure no other selections at other locations can take place
    # A lot of 2 seleciton constraints
    def add_onlyone_activitylocation_eachday_constraint(self, x: dict[tuple, Var]) -> None:
        print("add_onlyone_activitylocation_eachday_constraint")
        sessioncounter = 0
        for s in self.assigning_activities_problem.selections:
            sessioncounter = sessioncounter + 1
            if sessioncounter % 1000 == 0:
                print(sessioncounter)
            selections = self.assigning_activities_problem.get_all_selections_on_other_locations_for_different_activities_same_day(
                s
            )
            for s1 in selections:
                self.model += (
                    x[s] + x[s1] <= 1,
                    f"{s}_and_{s1}_excluded_because_different_location_same_day_{s.activity}",
                )

    #def add_max_nb_of_most_popular_activities_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
    def add_at_most_1_activity_out_of_camp(self, x: dict[tuple, Var]) -> None:
        print("add_at_most_1_activity_out_of_camp")
        grpcounter = 0
        for g in self.assigning_activities_problem.groups:
            grpcounter = grpcounter + 1
            if grpcounter % 25 == 0:
                print(g.id)
            selections = [
                s
                for s in self.assigning_activities_problem.selections
                if s.group == g and s.activity.in_camp == False
            ]
            # print (g.id)
            # print (selections)
            self.model += (
                xsum(x[s] for s in selections) <= 1,
                "group_" + g.id + "_at_most_1_activity_out_of_camp",
            )
        

    # find all activities where age does not match and force these to zero
    # this should not happen for any, as data is supposed to be cleaned, keep it as a check
    def add_age_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
        print("add_age_constraint")
        sessioncounter = 0
        printmsg = 1
        for s in self.assigning_activities_problem.selections:
            sessioncounter = sessioncounter + 1
            if sessioncounter % 1000 == 0:
                print(sessioncounter)
            if s.group.age_span.low >= s.activity.age_span.low and s.group.age_span.high <= s.activity.age_span.high:
                continue

            if printmsg == 1:
                print(
                    f"NOTE found selection where age group not with allowed ages {s.group.id} {s.activity.id}, this should not be the case, adding constraint to prevent assignment"
                )
                print("Remember this is disabled")
                printmsg = 0

            # self.model += (
            #      x[s] <= 0,
            #      f"group_{s.group.id}_does_not_have_age_required_for_{s.activity.id}_{s.time_slot.id}_{s.time_slot.startname()}",
            # )

    # find most popular activities and constrain to max_activities
    # another constraint will make sure at the most one session for one activity
    def add_max_nb_of_most_popular_activities_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
        print("add_max_nb_of_most_popular_activities_constraint - maxPopularActivities="+str(self.maxPopularActivities))
        grpcounter = 0
        for g in self.assigning_activities_problem.groups:
            grpcounter = grpcounter + 1
            if grpcounter % 25 == 0:
                print(g.id)
            selections = [
                s
                for s in self.assigning_activities_problem.selections
                if s.group == g and s.activity in self.assigning_activities_problem.popularactivities
            ]
            # print (g.id)
            # print (selections)
            self.model += (
                xsum(x[s] for s in selections) <= self.maxPopularActivities,
                "group_" + g.id + "_at_most_1_popular_activity",
            )


            
    # one group must have one activity
    def add_min_session_per_group_constraint(self, x: dict[tuple, Var]) -> None:
        print("add_min_session_per_group_constraint - minSessionsPerGroup="+str(self.minSessionsPerGroup))
        grpcounter = 0
        for g in self.assigning_activities_problem.groups:
            grpcounter = grpcounter + 1
            if grpcounter % 25 == 0:
                print(g.id)
            selections = [
                s for s in self.assigning_activities_problem.selections if s.group == g 
            ]
            self.model += (
                xsum(x[s] for s in selections) >=  self.minSessionsPerGroup,
                "group_" + g.id + "_min_sessions" ,
            )

                
     
    # one group must have atmost Y activities
    def add_max_sessions_per_group_constraint(self, x: dict[tuple, Var]) -> None:
        print("add_max_sessions_per_group_constraint - maxSessionsPerGroup="+str(self.maxSessionsPerGroup))
        grpcounter = 0
        for g in self.assigning_activities_problem.groups:
            grpcounter = grpcounter + 1
            if grpcounter % 25 == 0:
                print(g.id)
            selections = [
                s for s in self.assigning_activities_problem.selections if s.group == g 
            ]
            self.model += (
                xsum(x[s] for s in selections) <= self.maxSessionsPerGroup,
                "group_" + g.id + "_max_sessions" ,
            )



    # define the objective function
    def add_objective(self, x: dict[tuple, Var]) -> None:
        print("add objective")
        self.model.objective = maximize(xsum(s.priority * x[s] for s in self.assigning_activities_problem.selections))

        
    def to_dataframe(self):
        columns = ["minSessionsPerGroup","maxSessionsPerGroup", "maxSolveSeconds", "maxPopularActivities"]

        data = [
            [
                self.minSessionsPerGroup,
                self.maxSessionsPerGroup,
                self.maxSolveSeconds,
                self.maxPopularActivities
            ]
        ]
        return pd.DataFrame(data=data, columns=columns)

    def to_excel(self, filename: str, mode: str, sheet: str):
        df = self.to_dataframe()
        #append_df_to_excel(filename, df, sheet_name='properties', index=False)
        with pd.ExcelWriter(filename, engine='openpyxl', mode=mode) as writer:
            df.to_excel(writer,  sheet_name=sheet,index=False)
