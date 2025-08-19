# opti_scout
Project to optimize the allocation of scout groups to activities

## Project description

This project concerns the assigment of scout groups to specific activities:

> Assign each group `g` to a list of activities `a` according to the group's preferences

However, some activities are more popular than others, and so this becomes a selection problem.

This document has the following structure. First, we will describe the whole problem. Then, we will break down the approach to solving it into small pieces, which should be completed incrementally.

### Components

The problem has two major components: a group `g` and an activity `a`.

#### Group

A group has the following characteristics:

- Size, i.e. number of scouts
- Age
- List of ordered priorities
- Timeslots where the group can and cannot do activities

There are expected to be around 1300 groups.

#### Activity

An activity has the following characteristics:

- Size limit
- Age limit
- Duration
- Time window
- Location (optional)

There are expected to be around 150 activities.

### Constraints

- Age limit per activity
- Size limit per activity
- A group can attend one activity at a time
- Group timeslots have to be respected
- Activity time windows have to be respected
- Travel time between locations of different activities needs to possible, if applicable.

### Objectives

- Maximize the number of fulfilled priorities per group. A higher priority has more value, but not defined what it should be
- Distribute activities across the week
- Aim to keep the number of priorities fulfilled similar between groups

### Guide to development

To solve this problem, we need to develop both the mathematical as well as the code side of things:

#### Step 1 - Basic setup

For the math part, come up with a basic binary that describes a combination of group, activity and time.

For the code, create a simple function that solves this basic problem using the python-mip library.

#### Step 2 - Add some logic

For the math part, add the first two constraints

For the code part, create classes called `Group` and `Activity` which encaspulate the characteristics. Connect this to the basic model you wrote. Finally, write some tests for this.

#### Step 3 - Add the rest of the constraints

Add all the constraints to the model, both in math and code. Don't forget to test

#### Step 4 - Add a simple objective

Pick the first objective and implement it. Make it such that the priority values are easy to change

#### Step 5 - All objectives

Implement all objectives
