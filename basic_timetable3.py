from ortools.sat.python import cp_model

# ---------- Problem data ----------
days = ["Mon", "Tue", "Wed", "Thu", "Fri"]  # 5-day week
num_days = len(days)
max_slots_per_day = 6  # candidate slots per day (solver will try to minimize usage)
rooms = [f"Room{i+1}" for i in range(3)]  # 3 rooms
num_rooms = len(rooms)

# Courses 1..6 (use 0-based indices internally)
courses = [f"Course{i+1}" for i in range(6)]
num_courses = len(courses)

# Frequencies per week
course_freq = {
    0: 3,  # Course1 -> 3 times/week
    1: 3,  # Course2 -> 3 times/week
    2: 3,  # Course3 -> 3 times/week
    3: 3,  # Course4 -> 3 times/week
    4: 2,  # Course5 -> 2 times/week
    5: 2,  # Course6 -> 2 times/week
}

# Professors assignment
# Prof1 -> courses 1,3,6  (indices 0,2,5)
# Prof2 -> courses 2,4,5  (indices 1,3,4)
professors = ["Prof1", "Prof2"]
course_prof = {
    0: 0,
    1: 1,
    2: 0,
    3: 1,
    4: 1,
    5: 0,
}

# ---------- Model ----------
model = cp_model.CpModel()

# Decision variable:
# x[c, d, s, r] = 1 if course c is scheduled on day d, slot s (1..max_slots_per_day), in room r
x = {}
for c in range(num_courses):
    for d in range(num_days):
        for s in range(max_slots_per_day):
            for r in range(num_rooms):
                x[(c, d, s, r)] = model.NewBoolVar(f"x_c{c}_d{d}_s{s}_r{r}")

# y[d,s] = 1 if slot s on day d is used by any course (helps minimize used slots)
y = {}
for d in range(num_days):
    for s in range(max_slots_per_day):
        y[(d, s)] = model.NewBoolVar(f"y_d{d}_s{s}")

# ---------- Constraints ----------

# 1) Each course must appear exactly course_freq[c] times across the week
for c in range(num_courses):
    model.Add(
        sum(x[(c, d, s, r)]
            for d in range(num_days)
            for s in range(max_slots_per_day)
            for r in range(num_rooms)) == course_freq[c]
    )

# 2) A course has at most one session per day (no double-booking same course on same day)
for c in range(num_courses):
    for d in range(num_days):
        model.Add(
            sum(x[(c, d, s, r)]
                for s in range(max_slots_per_day)
                for r in range(num_rooms)) <= 1
        )

# 3) Room clash: at most one course in a given room at a given day+slot
for d in range(num_days):
    for s in range(max_slots_per_day):
        for r in range(num_rooms):
            model.Add(
                sum(x[(c, d, s, r)] for c in range(num_courses)) <= 1
            )

# 4) Professor clash: a professor cannot teach two courses at the same day+slot
for p in range(len(professors)):
    for d in range(num_days):
        for s in range(max_slots_per_day):
            model.Add(
                sum(
                    x[(c, d, s, r)]
                    for c in range(num_courses) if course_prof[c] == p
                    for r in range(num_rooms)
                ) <= 1
            )

# 5) Link x -> y: if any course is scheduled at (d,s) then y[d,s] must be 1
#    sum_c_r x[c,d,s,r] <= bigM * y[d,s], bigM = total courses * rooms (safe upper bound)
bigM = num_courses * num_rooms
for d in range(num_days):
    for s in range(max_slots_per_day):
        model.Add(
            sum(x[(c, d, s, r)] for c in range(num_courses) for r in range(num_rooms))
            <= bigM * y[(d, s)]
        )
        # also if y=1 then at least one x could be 1, but not strictly necessary:
        # model.Add(sum(...) >= y[(d,s)])  # optional (not needed for objective correctness)

# ---------- Objective ----------
# Minimize total used slots across the week (sum over days of used slots)
model.Minimize(sum(y[(d, s)] for d in range(num_days) for s in range(max_slots_per_day)))

# ---------- Solver ----------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30  # time limit (adjust as needed)
solver.parameters.num_search_workers = 8

status = solver.Solve(model)

# ---------- Output ----------
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    # Build an easy-to-read weekly grid: days x slots x rooms
    # We will print by day -> slot -> room
    print("Weekly schedule (Day -> Slot -> Room : Course (Prof))\n")
    for d in range(num_days):
        print(f"=== {days[d]} ===")
        for s in range(max_slots_per_day):
            # check whether this slot is actually used
            if solver.Value(y[(d, s)]) == 0:
                # skip printing unused slots to keep output compact
                continue
            row = []
            for r in range(num_rooms):
                found = False
                for c in range(num_courses):
                    if solver.Value(x[(c, d, s, r)]) == 1:
                        prof = professors[course_prof[c]]
                        row.append(f"{rooms[r]}: {courses[c]} ({prof})")
                        found = True
                        break
                if not found:
                    row.append(f"{rooms[r]}: -")
            print(f" Slot{s+1}: " + " | ".join(row))
        print()
    # Additionally print summary per course (which days/slots it is scheduled)
    print("Per-course schedule:")
    for c in range(num_courses):
        placements = []
        for d in range(num_days):
            for s in range(max_slots_per_day):
                for r in range(num_rooms):
                    if solver.Value(x[(c, d, s, r)]) == 1:
                        placements.append(f"{days[d]} Slot{s+1} in {rooms[r]}")
        print(f" {courses[c]:<8} -> {', '.join(placements)}")
else:
    print("No feasible solution found. Try increasing slots per day or relaxing constraints.")
