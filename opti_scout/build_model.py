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
        self.add_unavailable_time_constraint(x)
        self.add_age_constraint(x)
        self.add_outofcamp_activities_constraint(x)

        self.add_objective(x)

        return self.optimize()

    def generate_variables(self) -> dict[tuple, Var]:
        return {s: self.model.add_var(var_type=BINARY, name=str(s)) for s in self.assigning_activities_problem.selections}

    # any session of an activity cannot have more than the max number of participants
    def add_maxscout_constraint(self, x: dict[tuple, Var]) -> None:
        for a in self.assigning_activities_problem.activities:
            for session in a.available_sessions:
                selections = {s for s in self.selections if s.activity == a and session == s.time_slot}
                self.model += xsum(s.scout_group.size*x[s] for s in selections) <= a.max_participants

    # one group gets at most one session from any activity
    def add_max_1_session_constraint(self, x: dict[tuple, Var]) -> None:
        for g in self.assigning_activities_problem.scoutgroups:
            for a in self.assigning_activities_problem.activities:
                selections = [s for s in self.assigning_activities_problem.selections if s.scout_group == g and s.activity == a]
                self.model += xsum(x[s] for s in selections) <= 1, "group_" + g.identifier + "_at_most_1_session_for_activity_" + a.identifier

    # If a session falls outside the groups available hours, then force it to 0
    # This could be avoided if we only generated variables representing sessions in available timeslots for groups
    def add_unavailable_time_constraint(self, x: dict[tuple, Var]) -> list[tuple]:
        for s in self.assigning_activities_problem.selections:
            if s.scout_group.in_available_timeslots(s.time_slot):
                continue

            self.model += x[s] <= 0, f"groupDoesNotHaveAvailabletime_{s.scout_group.identifier}_{s.activity.identifier}_start{s.time_slot.startname()}"

    # find all activities where age does not match and force these to zero
    def add_age_constraint(self, x: dict[tuple, Var], unavailable: list[tuple]) -> list[tuple]:
        for s in self.assigning_activities_problem.selections:
            if s.scout_group.agegroup in s.activity.allowed_age_groups:
                continue

            self.model += x[s] <= 0, f"group_{s.scout_group.identifier}_does_not_have_age_required_for_{s.activity.identifier}_{s.time_slot.startname()}"

    # Any group having an out-of-camp session can do nothing else this day, no other out-of-camp or in-camp activities (kind of hard constraint, but reasonable)
    def add_outofcamp_activities_constraint(self, x: dict[tuple, Var]) -> None:
        for s in self.assigning_activities_problem.selections:
            if not s.activity.out_of_camp:
                continue
            
            selections = self.assigning_activities_problem.get_all_selections_on_same_day_but_different_activities(s)
            for s1 in selections:
                self.model += x[s] + x[s1]  <= 1, f"{s}_and_{s1}_excluded_for_out_of_camp_of_{s.activity}"              

    # define the objective function
    def add_objective(self, x: dict[tuple, Var]) -> None:
        self.model.objective = maximize(xsum(s.priority*x[s] for s in self.assigning_activities_problem.selections))

    # run the model optimization and report the solution
    def optimize(self) -> None:
        status = self.model.optimize(max_seconds=300)
        print(status)
        if status not in [OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE]:
            return None
        
        print("solution:")
        for var in self.model.vars:
            print(f"{var.name}: {var.x}")
