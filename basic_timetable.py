from ortools.sat.python import cp_model

# 1) Data
teachers = ["Prof A", "Prof B"]
courses = ["Math", "Physics"]
rooms = ["Room1", "Room2"]
slots = ["Morning", "Afternoon"]

model = cp_model.CpModel()

# 2) Decision variables: x[c, s, r] = course c in slot s, room r
x = {}
for c in range(len(courses)):
    for s in range(len(slots)):
        for r in range(len(rooms)):
            x[(c,s,r)] = model.NewBoolVar(f"x_c{c}_s{s}_r{r}")

# 3) Constraints
# Each course should happen exactly once
for c in range(len(courses)):
    model.Add(sum(x[(c,s,r)] for s in range(len(slots)) for r in range(len(rooms))) == 1)

# No room clashes (one course per room per slot)
for s in range(len(slots)):
    for r in range(len(rooms)):
        model.Add(sum(x[(c,s,r)] for c in range(len(courses))) <= 1)

# 4) Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("Timetable:")
    for c in range(len(courses)):
        for s in range(len(slots)):
            for r in range(len(rooms)):
                if solver.Value(x[(c,s,r)]) == 1:
                    print(f" Course {courses[c]} in {rooms[r]} at {slots[s]}")
else:
    print("No feasible solution.")
