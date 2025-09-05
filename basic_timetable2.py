from ortools.sat.python import cp_model
import random

# 1) Data
teachers = [f"Teacher {chr(65+i)}" for i in range(10)]  # A, B, C, ..., J
courses = [f"Course{i+1}" for i in range(20)]  # Course1 ... Course20
rooms = [f"Room{r+1}" for r in range(5)]  # Room1 ... Room5
slots = [f"Slot{s+1}" for s in range(8)]  # Slot1 ... Slot8

# Randomly assign each course to a teacher (0–9)
course_teacher = {c: random.randint(0, len(teachers)-1) for c in range(len(courses))}

# 2) Model
model = cp_model.CpModel()

# Decision variables: x[c,s,r] = 1 if course c is scheduled in slot s, room r
x = {}
for c in range(len(courses)):
    for s in range(len(slots)):
        for r in range(len(rooms)):
            x[(c,s,r)] = model.NewBoolVar(f"x_c{c}_s{s}_r{r}")

# 3) Constraints

# Each course exactly once
for c in range(len(courses)):
    model.Add(sum(x[(c,s,r)] for s in range(len(slots)) for r in range(len(rooms))) == 1)

# No room clash (at most one course per slot per room)
for s in range(len(slots)):
    for r in range(len(rooms)):
        model.Add(sum(x[(c,s,r)] for c in range(len(courses))) <= 1)

# No teacher clash (a teacher can teach at most one course per slot)
for t in range(len(teachers)):
    for s in range(len(slots)):
        model.Add(sum(x[(c,s,r)] 
                      for c in range(len(courses)) if course_teacher[c] == t
                      for r in range(len(rooms))) <= 1)

# 4) Solve
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8   # parallelism
solver.parameters.max_time_in_seconds = 30  # optional time limit

status = solver.Solve(model)

# 5) Print solution
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Generated Timetable:\n")
    for c in range(len(courses)):
        for s in range(len(slots)):
            for r in range(len(rooms)):
                if solver.Value(x[(c,s,r)]) == 1:
                    teacher = teachers[course_teacher[c]]
                    print(f"{courses[c]:<10} taught by {teacher:<10} "
                          f"in {rooms[r]:<6} at {slots[s]}")
else:
    print("No feasible solution found.")
