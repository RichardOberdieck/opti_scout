from opti_scout.classes import AssigningActivititesProblem
from pydantic import BaseModel
from mip import BINARY, xsum, Model, maximize, OptimizationStatus, Var


class ModelBuilder(BaseModel, arbitrary_types_allowed=True):
    assigning_activities_problem: AssigningActivititesProblem
    model: Model

    @classmethod
    def create(cls, assigning_activities_problem: AssigningActivititesProblem) -> "ModelBuilder":
        return cls(assigning_activities_problem=assigning_activities_problem, model=Model())

    def solve(self):
        x = self.generate_variables()

        self.add_maxscout_constraint(x)
        self.add_max_1_session_constraint(x)
        self.add_max_1_of_overlapping_sessions_constraint(x)
        unavailable = self.add_unavailable_time_constraint(x)
        unavailable = self.add_age_constraint(x, unavailable)
        self.add_outofcamp_activities_constraint(x)

        self.add_objective(x)

        return optimize_model(self.model, unavailable)

    def generate_variables(self) -> dict[tuple, Var]:
        print("Generate variables")
        x = {s: self.model.add_var(var_type=BINARY, name=str(s)) for s in self.assigning_activities_problem.selections}
        print("Variable generated:", len(x))
        return x

    # any session of an activity cannot have more than the max number of participants
    def add_maxscout_constraint(self, x: dict[tuple, Var]) -> None:
        for a in self.assigning_activities_problem.activities:
            for s in a.available_sessions:
                self.model += xsum(s.scout_group.size*x[s] for s in self.assigning_activities_problem.get_selections_for_activity(a, s)) <= a.max_participants

    # one group gets at most one session from any activity
    def add_max_1_session_constraint(self, x: dict[tuple, Var]) -> None:
        lhs = []
        for g in self.assigning_activities_problem.scoutgroups:
            for p in g.priorities:
                activity = p.activity
                lhs.clear()
                for s in activity.available_sessions:
                    lhs.append(x[(g.identifier, activity.identifier, s.startname())])
                # only need to add constraint if there is more than one
                if len(lhs) > 1:
                    name = "group_" + g.identifier + "_at_most_1_session_for_activity_" + activity.identifier
                    self.model += xsum(lhs) <= 1, name

    # any group can at most  have 1 session of overlapping sessions across all activities that they have prioritized
    def add_max_1_of_overlapping_sessions_constraint(self, x: dict[tuple, Var]) -> None:
        lhs = []
        for g in self.assigning_activities_problem.scoutgroups:
            for p in g.priorities:
                a = p.activity
                for s in a.available_sessions:
                    lhs.clear()
                    lhs.append(x[(g.identifier, a.identifier, s.startname())])
                    for p1 in g.priorities:
                        # check against all other priority sessions
                        a1 = p1.activity
                        if a != a1:
                            for s1 in a1.available_sessions:
                                if s.overlaps(s1):
                                    lhs.append(x[(g.identifier, a1.identifier, s1.startname())])
                    if len(lhs) > 1:
                        name = (
                            "group_"
                            + g.identifier
                            + "_can_only_attend_one_of_these_as_they_overlap_in_time_"
                            + s.startname()
                        )
                        print(name, "nb of vars: ", len(lhs))
                        self.model += xsum(lhs) <= 1, name

    # If a session falls outside the groups available hours, then force it to 0
    # This could be avoided if we only generated variables representing sessions in available timeslots for groups
    def add_unavailable_time_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
        u = []
        for g in self.assigning_activities_problem.scoutgroups:
            # get all timeslots for one group
            for p in g.priorities:
                a = p.activity
                # loop over all available session for this priority
                for s in a.available_sessions:
                    # group cannot attend session until we have found that this session is within the available times for the group
                    if g.InAvailableTimeslots(s) is False:
                        name = (
                            "groupDoesNotHaveAvailabletime_"
                            + g.identifier
                            + "_"
                            + a.identifier
                            + "_start"
                            + s.startname()
                        )
                        print("False session InAvailableTimeslot genereate constraint: ", name)
                        # store list of vars set to 0 as they are in unavailable times for the group
                        u.append((x[(g.identifier, a.identifier, s.startname())], name))
                        # create actual constraint
                        self.model += x[(g.identifier, a.identifier, s.startname())] <= 0, name
                    else:
                        print("True session InAvailableTimeslot no consgtraint needed")
        return u

    # find all activities where age does not match and force these to zero
    def add_age_constraint(self, x: dict[tuple, Var], unavailable: list[tuple]) -> list[tuple]:
        for a in self.assigning_activities_problem.activities:
            for s in a.available_sessions:
                for g in self.assigning_activities_problem.scoutgroups:
                    if g.hasActivity(a) and g.agegroup not in a.allowed_age_groups:
                        name = (
                            "group_"
                            + g.identifier
                            + "_does_not_have_age_required_for_"
                            + a.identifier
                            + "_"
                            + s.startname()
                        )
                        self.model += x[(g.identifier, a.identifier, s.startname())] <= 0, name
                        unavailable.append((x[(g.identifier, a.identifier, s.startname())], name))
        return unavailable

    # Any group having an out-of-camp session can do nothing else this day, no other out-of-camp or in-camp activities (kind of hard constraint, but reasonable)
    def add_outofcamp_activities_constraint(self, x: dict[tuple, Var]) -> None:
        for g in self.assigning_activities_problem.scoutgroups:
            for p in g.priorities:
                a = p.activity
                if a.out_of_camp:
                    # This will generate to many constraints if any other outofcamp activities are prioritiezed
                    print(
                        g.identifier,
                        "has out of camp activity (any session selected should prevent any other activities on the same day):",
                        a.identifier,
                    )
                    # we could just loop through the remaining priorities as the previous ones has been checked
                    for p1 in g.priorities:
                        a1 = p1.activity
                        if a.identifier != a1.identifier:
                            for s in a.available_sessions:
                                # print("session:",a.identifier,s.startname())
                                for s1 in a1.available_sessions:
                                    if s.sameday(s1):
                                        # print("SAME DAY:",a1.identifier,s1.startname())
                                        name = (
                                            "group_"
                                            + g.identifier
                                            + "_out_of_camp_constraint_"
                                            + a.identifier
                                            + "_"
                                            + s.startname()
                                            + "_"
                                            + a1.identifier
                                            + "_"
                                            + s1.startname()
                                        )
                                        print(name)
                                        self.model += (
                                            x[(g.identifier, a.identifier, s.startname())]
                                            + x[(g.identifier, a1.identifier, s1.startname())]
                                            <= 1,
                                            name,
                                        )

    # define the objective function
    def add_objective(self, x: dict[tuple, Var]) -> None:
        lhs = []
        for g in self.assigning_activities_problem.scoutgroups:
            for p in g.priorities:
                activity = p.activity
                for s in activity.available_sessions:
                    lhs.append(p.value * x[(g.identifier, activity.identifier, s.startname())])
        print("Define objective function using all vars included")
        self.model.objective = maximize(xsum(lhs))


# run the model optimization and report the solution
def optimize_model(model: Model, unavailable: list[tuple]) -> None:
    status = model.optimize(max_seconds=300)
    print(status)
    if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
        # print(u)
        print("solution:")
        for var in model.vars:
            # if this was set to zero for any reason and report as part of the solution
            for i in range(len(unavailable)):
                if var.name == unavailable[i][0].name:
                    print("Next forced to zero as", unavailable[i][1])
            print("{} : {}".format(var.name, var.x))
