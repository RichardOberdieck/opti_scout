import json
from pydantic import BaseModel, TypeAdapter, field_validator, model_validator
import pandas as pd
from mip import OptimizationStatus, Var

from datetime import datetime, timedelta
from collections import Counter

class age_span(BaseModel):
    low: int
    high: int

    def __str__(self):
        return "low, high"
   

class Timeslot(BaseModel):
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def start_before_end(self):
        if self.start >= self.end:
            raise ValueError("Start time has to be before the end time")
        return self

    def startname(self):
        return self.start.strftime("%Y_%m_%d_%H%M")

    def __eq__(self, other):
        if isinstance(other, Timeslot):
            return self.start == other.start and self.end == other.end
        else:
            return False

    def __hash__(self):
        return hash(self.start) + hash(self.end)

    def overlaps(self, other):
        return self.start < other.end and self.end > other.start

    def contains(self, other: "Timeslot") -> bool:
        return self.start <= other.start and self.end >= other.end

    def is_same_day(self, other: "Timeslot") -> bool:
        # TODO: are there multi-day activities, where we have to do contains-style things??
        return (self.start.date() in [other.start.date(), other.end.date()]) or (
            self.end.date() in [other.start.date(), other.end.date()]
        )


class ActivityTimeslot(BaseModel):
    id: str
    start: datetime
    end: datetime
    capacity: int

    @model_validator(mode="after")
    def start_before_end(self):
        if self.start >= self.end:
            raise ValueError("Start time has to be before the end time")
        return self

   
    def startname(self):
        return 'id:'+self.id+'start'+self.start.strftime('%Y-%m-%d-%H%M')+'_end'+self.end.strftime('%Y-%m-%d-%H%M')
        #return self.start.strftime("%Y_%m_%d_%H%M")

    def __eq__(self, other):
        if isinstance(other, ActivityTimeslot):
            return self.start == other.start and self.end == other.end
        else:
            return False

    def __hash__(self):
        return hash(self.start) + hash(self.end)

    def overlaps(self, other):
        return self.start < other.end and self.end > other.start

    def contains(self, other):
        # Checks if this timeslot contains the entirety of another timeslot or a datetime
        if isinstance(other, ActivityTimeslot):
            return self.start <= other.start and other.end <= self.end
        elif isinstance(other, datetime):
            return self.start <= other <= self.end
        else:
            raise TypeError("argument of invalid type '{}'".format(type(other)))

    def is_same_day(self, other: "ActivityTimeslot") -> bool:
        # TODO: are there multi-day activities, where we have to do contains-style things??
        return (self.start.date() in [other.start.date(), other.end.date()]) or (
            self.end.date() in [other.start.date(), other.end.date()]
        )
    

class Activity(BaseModel):
    id: str
    name: str
    age_span: age_span
    timeslots: set[ActivityTimeslot]
    activity_area: str
    in_camp: bool

    @field_validator("timeslots", mode="after")
    @classmethod
    def ensure_sessions_do_not_overlap(cls, sessions: set[ActivityTimeslot]) -> set[ActivityTimeslot]:
        for s in sessions:
            for t in sessions:
                if s != t and s.overlaps(t):
                    raise ValueError(f"Activity sessions overlap: {s} and {t}")
        return sessions

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return  self.id

    def __hash__(self):
        return hash(self.id)


    #maybe add check that no timeslots overlap
    
   
    #priorities: list[str]

class Group(BaseModel):
    id: str
    size: int
    age_span: age_span
    available: set[Timeslot]
    
    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id
    
    def __hash__(self):
        return hash(self.id)

    def in_available_timeslots(self, ActivityTimeslot):
        for t in self.available:
            if t.contains(ActivityTimeslot):
                return True
        return False       



class Selection(BaseModel):
    group: Group
    activity: Activity
    time_slot: ActivityTimeslot
    priority: int

    def __str__(self):
        return self.group.id + "_" + self.activity.id + '_' + self.time_slot.id

    def __hash__(self):
        return hash(self.group) + 3*hash(self.activity) + 5*hash(self.time_slot) + 9*hash(self.priority)


list_activities_adapter = TypeAdapter(list[Activity])
list_group_adapter = TypeAdapter(list[Group])


class AssigningActivititesProblem(BaseModel):
    activities: list[Activity]
    groups: list[Group]
    selections: set[Selection]
    popularactivities: list[Activity]

    @classmethod
    def from_json(cls, file_name: str) -> "AssigningActivititesProblem":
        with open(file_name, "r") as file:
            data = json.load(file)

        #to accomodate travel time add 30 min to each activity session duration and each group available time (to accomodate for longer session)
        travelminutes=30

        date_format = '%Y-%m-%dT%H:%M:%SZ'
        for a in data["activities"]:
            for t in a["timeslots"]:
               t["end"] = (datetime.strptime(t["end"], date_format) + timedelta(minutes=travelminutes)).strftime(date_format)
            
        for g in data["groups"]:
            for a in g["available"]:
               a["end"] = (datetime.strptime(a["end"], date_format) + timedelta(minutes=travelminutes)).strftime(date_format)


        # Create named directory of activities
        acts = {}
        for i in data["activities"]:
            acts[i["id"]] = i

        # Create named directory of priorities, which are selected activities for each group
        priorities = {}
        popular=[]
        for g in data["groups"]:
            #start with priority 20 for each group
            priocounter=20
            for a in g["priorities"]:
                priorities[g["id"]+a] = priocounter
                priocounter=priocounter-1
                popular.append(a)
        #we could extend this to include ties
        #add nb most common as input to function from_json
        most_common = Counter(popular).most_common(2)  

        top_activities = [item for item, count in most_common]
        
        list_activities = list_activities_adapter.validate_python(data["activities"])
        list_groups = list_group_adapter.validate_python(data["groups"])

        toppop = []
        for a in list_activities:
            if a.id in top_activities:
                toppop.append(a)

        data["popularactivities"] = toppop

        # Create named directory of selections, selections are actual sessions for each of the activities that groups have prioritized == variables in the model
        selections = []
        
        for group in list_groups:
            for activity in list_activities:
                if group.id + activity.id in priorities:
                    for time_slot in activity.timeslots:
                        selections.append(
                            Selection(group=group, activity=activity, time_slot=time_slot, priority=priorities[group.id + activity.id])
                        )


        data["selections"] = selections
        
        if 'debug'  == 'nodebug':
            print ("printing groups")
            print (data["groups"])
    
            print ("printing activities")
            print (data["activities"])
        
            print ("printing selections")
            #print (data["selections"])
            for s in data["selections"]:
                print (s)


        

        return cls(**data)




    def get_popular_activities(self) -> list[Activity]:
        return {a for a in self.popularactivities}

    def get_selections_for_activity(self, activity: Activity, time_slot: ActivityTimeslot) -> set[Selection]:
        return {s for s in self.selections if s.activity == activity and time_slot == s.time_slot}

    def get_overlapping_selections(self, selection: Selection) -> list[Selection]:
        overlaps = []
        for s in self.selections:
            if s.group != selection.group:
                continue

            if s.activity == selection.activity:
                continue

            if selection.time_slot.overlaps(s.time_slot):
                overlaps.append(s)

        return overlaps

    def get_all_selections_on_other_locations_for_different_activities_same_day(self, selection: Selection) -> list[Selection]:
        selections = []
        for s in self.selections:
            #only look for this group
            if s.group != selection.group:
                continue
            #only allow other activitites
            if s.activity == selection.activity:
                continue
            #only find different locations
            if s.activity.activity_area == selection.activity.activity_area:
                continue

            if selection.time_slot.is_same_day(s.time_slot):
                selections.append(s)

        return selections
    

class Solution(BaseModel):
    selections: set[Selection]
    status: OptimizationStatus

    @classmethod
    def build(cls, variables: dict[Selection, Var], status: OptimizationStatus) -> "Solution":
        if status not in [OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE]:
            return cls(selections=set(), status=status)
        print(status)

        print("solution:")
        selections = []
        for selection, variable in variables.items():
            print(f"{variable.name}: {variable.x}")
            if variable.x > 0.5:
                selections.append(selection)

        return cls(selections=selections, status=status)

    def is_valid(self) -> bool:
        return len(self.selections) > 0

    def to_dataframe(self):
        columns = ["Scout Group", "Activity", "Timeslot","Start","End","Location","Priority"]

        data = [[s.group.id, s.activity.id, s.time_slot.id, s.time_slot.start.replace(tzinfo=None), s.time_slot.end.replace(tzinfo=None), s.activity.activity_area, s.priority] for s in self.selections]
        return pd.DataFrame(data=data, columns=columns)

    def to_excel(self, filename: str):
        df = self.to_dataframe()
        df.sort_values(by=['Scout Group','Start'], inplace=True)
        df.to_excel(filename)

    def create_gantt_chart(self) -> None:
        pass


    