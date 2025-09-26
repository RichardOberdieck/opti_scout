import json
from pydantic import BaseModel, TypeAdapter, field_validator, model_validator

from datetime import datetime


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

    def is_same_day(self, other: "Timeslot") -> bool:
        # TODO: are there multi-day activities, where we have to do contains-style things??
        return (self.start.date() in [other.start.date(), other.end.date()]) or (
            self.end.date() in [other.start.date(), other.end.date()]
        )


class Activity(BaseModel):
    name: str
    identifier: str
    allowed_age_groups: set[int]
    max_participants: int
    available_sessions: set[Timeslot]
    out_of_camp: bool

    @field_validator("available_sessions", mode="after")
    @classmethod
    def ensure_sessions_do_not_overlap(cls, sessions: set[Timeslot]) -> set[Timeslot]:
        for s in sessions:
            for t in sessions:
                if s != t and s.overlaps(t):
                    raise ValueError(f"Activity sessions overlap: {s} and {t}")
        return sessions

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __str__(self):
        return self.name + "(id:" + self.identifier + "," + self.location + ")"

    def __hash__(self):
        return hash(self.identifier)


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


class Selection(BaseModel):
    scout_group: ScoutGroup
    activity: Activity
    time_slot: Timeslot
    priority: int

    def __str__(self):
        return self.scout_group.identifier + "_" + self.activity.identifier + "_start" + self.time_slot.startname()

    def __hash__(self):
        return hash(self.scout_group) + 3 * hash(self.activity) + 5 * hash(self.time_slot) + 9 * hash(self.priority)


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
                priorities[i["identifier"] + p["activity"]] = p["value"]

        list_activities = list_activities_adapter.validate_python(data["activities"])
        list_scout_groups = list_scout_group_adapter.validate_python(data["scoutgroups"])

        selections = []
        for scout_group in list_scout_groups:
            for activity in list_activities:
                if scout_group.identifier + activity.identifier in priorities:
                    for time_slot in activity.available_sessions:
                        selections.append(
                            Selection(
                                scout_group=scout_group,
                                activity=activity,
                                time_slot=time_slot,
                                priority=priorities[scout_group.identifier + activity.identifier],
                            )
                        )

        data["selections"] = selections

        return cls(**data)

    def get_selections_for_activity(self, activity: Activity, time_slot: Timeslot) -> set[Selection]:
        return {s for s in self.selections if s.activity == activity and time_slot == s.time_slot}

    def get_overlapping_selections(self, selection: Selection) -> list[Selection]:
        overlaps = []
        for s in self.selections:
            if s.scout_group != selection.scout_group:
                continue

            if s.activity == selection.activity:
                continue

            if selection.time_slot.overlaps(s.time_slot):
                overlaps.append(s)

        return overlaps

    def get_all_selections_on_same_day_but_different_activities(self, selection: Selection) -> list[Selection]:
        selections = []
        for s in self.selections:
            if s.scout_group != selection.scout_group:
                continue

            if s.activity == selection.activity:
                continue

            if selection.time_slot.is_same_day(s.time_slot):
                selections.append(s)

        return selections
