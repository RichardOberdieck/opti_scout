import json
from pydantic import BaseModel, TypeAdapter

from datetime import datetime


# https://github.com/ErikBjare/timeslot/blob/master/src/timeslot/timeslot.py
class Timeslot(BaseModel):
    start: datetime
    end: datetime

    # Inspired by: http://www.codeproject.com/Articles/168662/Time-Period-Library-for-NET
    @classmethod
    def create(cls, start, end):
        return cls(start=start, end=end)

    def __str__(self):
        return "<Timeslot(start={}, end={})>".format(self.start, self.end)

    def startname(self):
        return self.start.strftime("%Y_%m_%d_%H%M")

    def __eq__(self, other):
        if isinstance(other, Timeslot):
            return self.start == other.start and self.end == other.end
        else:
            return False

    def __hash__(self):
        return hash(self.start) + hash(self.end)

    def duration(self):
        return self.end - self.start

    def overlaps(self, other):
        """Checks if this timeslot is overlapping partially or entirely with another timeslot"""
        return self.start <= other.start < self.end or self.start < other.end <= self.end or self in other

    def sameday(self, other):
        return (
            self.start.date() == other.start.date()
            or self.end.date() == other.end.date()
            or self.start.date() == other.end.date()
            or self.end.date() == other.start.date()
        )

    def contains(self, other):
        """Checks if this timeslot contains the entirety of another timeslot or a datetime"""
        if isinstance(other, Timeslot):
            return self.start <= other.start and other.end <= self.end
        elif isinstance(other, datetime):
            return self.start <= other <= self.end
        else:
            raise TypeError("argument of invalid type '{}'".format(type(other)))

    def __lt__(self, other):
        # implemented to easily allow sorting of a list of timeslots
        if isinstance(other, Timeslot):
            return self.start < other.start
        else:
            raise TypeError("operator not supported between instaces of '{}' and '{}'".format(type(self), type(other)))

    def gap(self, other):
        """If slots are separated by a non-zero gap, return the gap as a new timeslot, else None"""
        if self.end < other.start:
            return Timeslot(start=self.end, end=other.start)
        elif other.end < self.start:
            return Timeslot(start=other.end, end=self.start)
        else:
            return None


class Activity(BaseModel):
    name: str
    identifier: str
    allowed_age_groups: set[int]
    max_participants: int
    available_sessions: set[Timeslot]
    out_of_camp: bool

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __str__(self):
        return self.name + "(id:" + self.identifier + "," + self.location + ")"

    def __hash__(self):
        return hash(self.identifier)

    # maybe add check that no timeslots overlap


class ScoutGroup(BaseModel):
    name: str
    identifier: str
    agegroup: int
    size: int
    available_timeslots: set[Timeslot]

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __str__(self):
        return self.name + "(id:" + self.identifier + ")"

    def __hash__(self):
        return hash(self.identifier)

    def in_available_timeslots(self, timeslot):
        for t in self.available_timeslots:
            if t.contains(timeslot):
                return True
        return False

    # maybe add check that no timeslots overlap


class Selection(BaseModel):
    scout_group: ScoutGroup
    activity: Activity
    time_slot: Timeslot
    priority: int

    def __str__(self):
        return self.scout_group.identifier + "_" + self.activity.identifier + "_start" + self.time_slot.startname()

    def __hash__(self):
        return hash(self.scout_group) + 3*hash(self.activity) + 5*hash(self.time_slot) + 9*hash(self.priority)

list_activities_adapter = TypeAdapter(list[Activity])
list_scout_group_adapter = TypeAdapter(list[ScoutGroup])


class AssigningActivititesProblem(BaseModel):
    activities: list[Activity]
    scoutgroups: list[ScoutGroup]
    selections: set[Selection]

    @classmethod
    def from_json(cls, file_name: str) -> "AssigningActivititesProblem":
        with open(file_name, "r") as file:
            data = json.load(file)

        # Create named directory of activities
        acts = {}
        for i in data["activities"]:
            acts[i["identifier"]] = i

        priorities = {}
        for i in data["scoutgroups"]:
            for p in i["priorities"]:
                priorities[i["identifier"]+p["activity"]] = p["value"]

        list_activities = list_activities_adapter.validate_python(data["activities"])
        list_scout_groups = list_scout_group_adapter.validate_python(data["scoutgroups"])

        selections = []
        for scout_group in list_scout_groups:
            for activity in list_activities:
                if scout_group.identifier + activity.identifier in priorities:
                    for time_slot in activity.available_sessions:
                        selections.append(
                            Selection(scout_group=scout_group, activity=activity, time_slot=time_slot, priority=priorities[scout_group.identifier + activity.identifier])
                        )

        data["selections"] = selections

        return cls(**data)

    def get_selections_for_activity(self, activity: Activity, time_slot: Timeslot) -> set[Selection]:
        return {s for s in self.selections if s.scout_group.hasActivity(activity) and time_slot == s.time_slot}