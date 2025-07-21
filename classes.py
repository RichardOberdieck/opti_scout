
from pydantic import BaseModel
import numpy as np
import pandas as pd

from datetime import datetime, timedelta
from typing import Optional, Union

# https://github.com/ErikBjare/timeslot/blob/master/src/timeslot/timeslot.py
class Timeslot(BaseModel):
    start: datetime
    end: datetime

    # Inspired by: http://www.codeproject.com/Articles/168662/Time-Period-Library-for-NET
    def create(cls, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return "<Timeslot(start={}, end={})>".format(self.start, self.end)

    def startname(self):
        return self.start.strftime('%Y_%m_%d_%H%M')

    def __eq__(self, other) :
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
        return (
            self.start <= other.start < self.end
            or self.start < other.end <= self.end
            or self in other
        )

    def sameday(self, other):
        return (self.start.date() == other.start.date() 
                or self.end.date() == other.end.date()
                or self.start.date() == other.end.date()
                or self.end.date() == other.start.date())
    

    def contains(self, other) :
        """Checks if this timeslot contains the entirety of another timeslot or a datetime"""
        if isinstance(other, Timeslot):
            return self.start <= other.start and other.end <= self.end
        elif isinstance(other, datetime):
            return self.start <= other <= self.end
        else:
            raise TypeError("argument of invalid type '{}'".format(type(other)))


    
    def __lt__(self, other) :
        # implemented to easily allow sorting of a list of timeslots
        if isinstance(other, Timeslot):
            return self.start < other.start
        else:
            raise TypeError(
                "operator not supported between instaces of '{}' and '{}'".format(
                    type(self), type(other)
                )
            )

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
        return self.name + '(id:' + self.identifier+"," + self.location + ")"

    def __hash__(self):
        return hash(self.identifier)

    #maybe add check that no timeslots overlap
    
    
class priority(BaseModel):
    activity: Activity
    value: int

    def __eq__(self, other):
        return self.Activity == other.Activity and self.value == other.value

    def __hash__(self):
        return hash(self.value) 

    # no activities must have the same priority for a scoutgroup

class ScoutGroup(BaseModel):
    name: str
    identifier: str
    agegroup: int
    size: int
    available_timeslots: set[Timeslot]
    priorities: set[priority]
    
    def __eq__(self, other):
        return self.identifier == other.identifier

    def __str__(self):
        return self.name + '(id:' + self.identifier + ")"

    def hasActivity(self, activity):
        return any(activity == p.activity for p in self.priorities)
    
    def InAvailableTimeslots(self, timeslot):
        for t in self.available_timeslots:
            if t.contains(timeslot):
              return True
        return False          

    #maybe add check that no timeslots overlap



class Parameters(BaseModel):
    parm1: float
    parm2: int



class AssigningActivititesProblem(BaseModel):
    activities: list[Activity]
    scoutgroups: list[ScoutGroup]
    parameters: Parameters    
