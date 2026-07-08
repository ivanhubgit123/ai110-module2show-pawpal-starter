# 🐾 PawPal+

PawPal+ is a pet-care scheduling assistant. It helps a busy owner track care tasks
across multiple pets (walks, feeding, grooming, vet visits, enrichment), respects
constraints like available time and priority, and generates an explained daily plan.

The project ships as a **Python logic layer** (`pawpal_system.py`), a **CLI demo**
(`main.py`), a **Streamlit UI** (`app.py`), and an **automated test suite**
(`tests/test_pawpal.py`).

## ✨ Features

- **Multi-pet task tracking** — one `Owner` → many `Pet`s → many `Task`s.
- **Time & priority sorting** — chronological, or priority-first (High → Medium → Low).
- **Filtering** — by pet, completion status, or frequency.
- **Conflict detection** — flags tasks booked at the same time, even across pets.
- **Recurring tasks** — daily/weekly tasks auto-schedule their next occurrence on completion.
- **Explained daily plan** — fits tasks into a time budget, priority-first, and says why.
- **Next available slot** — finds the earliest open gap that fits a new task.
- **Data persistence** — saves and reloads the whole owner/pet/task tree to `data.json`.
- **Formatted CLI output** — `tabulate` tables with emoji priority/type indicators.

## 🏗️ Architecture

| File | Role |
|------|------|
| `pawpal_system.py` | Domain model + scheduling logic: `Task`, `Pet`, `Owner`, `Scheduler` |
| `main.py` | CLI demo that exercises every capability and prints formatted tables |
| `app.py` | Streamlit UI for adding pets/tasks and viewing the generated plan |
| `tests/test_pawpal.py` | Pytest suite (14 tests) covering the core scheduling behaviors |
| `data.json` | Persisted owner/pet/task data (generated on save) |

## 🚀 Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the CLI demo

```bash
python main.py
```

### Run the Streamlit app

```bash
streamlit run app.py
```

### Run the tests

```bash
python -m pytest          # or: python -m pytest --cov
```

## 🖥️ Sample Output

Running `python main.py` prints the full demo. Real output (emoji priority and
task-type indicators rendered with `tabulate`):

```
Today's Schedule (sorted by time)
=================================
Done    Type    Time    Pet      Task             Duration    Priority    Frequency
------  ------  ------  -------  ---------------  ----------  ----------  -----------
⬜       🚶       08:00   Biscuit  Morning walk     30 min      🔴 high      daily
⬜       🍖       08:00   Biscuit  Feeding          10 min      🔴 high      once
⬜       🪥       08:00   Mochi    Morning brush    15 min      🟡 medium    once
⬜       ✂️      09:00   Mochi    Grooming         40 min      🟢 low       once
⬜       🍖       18:00   Mochi    Evening feeding  10 min      🟡 medium    once
```

## ⚙️ Advanced Capability — Next Available Slot (Challenge 1)

Beyond sorting and filtering, `Scheduler.find_next_available_slot()` answers a
different question: *"Where can I fit a new task today?"* It treats every existing
task as a busy interval `[start, start + duration)`, walks them in chronological
order, and returns the first gap (as `HH:MM`) large enough to hold the requested
duration — or `None` if the day has no room.

```
Next Available Slot Demo
------------------------
  Next available 20-minute slot today: 08:30
```

With back-to-back tasks at 08:00 (30 min), 08:00 (10 min), and 08:00 (15 min),
the earliest 20-minute opening is 08:30, right after the busiest block clears.

## 💾 Data Persistence (Challenge 2)

PawPal+ remembers pets and tasks between runs by serializing the full object tree
to `data.json`.

**Persistence workflow:**

1. Each domain class exposes a `to_dict()` / `from_dict()` pair that converts
   itself (and its children) to and from plain JSON-friendly dictionaries. This
   is the **custom dictionary conversion** approach — no external library needed.
   The only non-primitive field, `Task.date`, is stored with `date.isoformat()`
   and rebuilt with `date.fromisoformat()`.
2. `Owner.save_to_json("data.json")` calls `owner.to_dict()` and writes it with
   `json.dump(..., indent=2)`.
3. `Owner.load_from_json("data.json")` reads the file with `json.load()` and
   rebuilds a fully-typed `Owner` (with its `Pet`s and `Task`s) via `from_dict()`.

```
Data Persistence Demo
---------------------
  Saved current owner, pets, and tasks to data.json.
  Reloaded owner 'Alex' with 2 pets and 6 total tasks.
```

**Files modified for persistence:** `pawpal_system.py` (added `to_dict` /
`from_dict` to `Task`, `Pet`, and `Owner`, plus `Owner.save_to_json` /
`Owner.load_from_json`, and `import json`); `main.py` (added the save → reload
demo); `tests/test_pawpal.py` (added a save/load round-trip test).

## 🥇 Priority-Based Scheduling (Challenge 3)

Every `Task` carries a `priority` of `"low"`, `"medium"`, or `"high"`.
`Scheduler.sort_by_priority_then_time()` sorts by priority **first**, then by time
within each priority band, using the `PRIORITY_ORDER = {"high": 0, "medium": 1,
"low": 2}` map as the sort key. `generate_plan()` uses this same ordering so the
time budget is spent on the most important tasks first.

Sorting the **same** task list two ways makes the difference obvious — note how
the low-priority 09:00 Grooming drops *below* the medium-priority 18:00 feeding:

```
Today's Schedule (sorted by time)
=================================
Done    Type    Time    Pet      Task             Duration    Priority    Frequency
------  ------  ------  -------  ---------------  ----------  ----------  -----------
⬜       🚶       08:00   Biscuit  Morning walk     30 min      🔴 high      daily
⬜       🍖       08:00   Biscuit  Feeding          10 min      🔴 high      once
⬜       🪥       08:00   Mochi    Morning brush    15 min      🟡 medium    once
⬜       ✂️      09:00   Mochi    Grooming         40 min      🟢 low       once
⬜       🍖       18:00   Mochi    Evening feeding  10 min      🟡 medium    once

Today's Schedule (sorted by priority, then time)
================================================
Done    Type    Time    Pet      Task             Duration    Priority    Frequency
------  ------  ------  -------  ---------------  ----------  ----------  -----------
⬜       🚶       08:00   Biscuit  Morning walk     30 min      🔴 high      daily
⬜       🍖       08:00   Biscuit  Feeding          10 min      🔴 high      once
⬜       🪥       08:00   Mochi    Morning brush    15 min      🟡 medium    once
⬜       🍖       18:00   Mochi    Evening feeding  10 min      🟡 medium    once
⬜       ✂️      09:00   Mochi    Grooming         40 min      🟢 low       once
```

The daily plan then fills the time budget high-priority-first:

```
Generated Daily Plan
--------------------
  Time budget: 55 / 60 minutes used
  - Included Biscuit's 'Morning walk' at 08:00 (priority: high, 30 min).
  - Included Biscuit's 'Feeding' at 08:00 (priority: high, 10 min).
  - Included Mochi's 'Morning brush' at 08:00 (priority: medium, 15 min).
  - Skipped Mochi's 'Evening feeding' — not enough time remaining (priority: medium, 10 min).
  - Skipped Mochi's 'Grooming' — not enough time remaining (priority: low, 40 min).
```

## 🎨 Professional UI & Output Formatting (Challenge 4)

The CLI in `main.py` uses **[`tabulate`](https://pypi.org/project/tabulate/)** to
render aligned tables (`tablefmt="simple"`) plus emoji indicators for at-a-glance
scanning:

| Feature | Where | How |
|---------|-------|-----|
| Structured CLI tables | `print_schedule()` | `tabulate(rows, headers=..., tablefmt="simple")` |
| Color-coded priority indicators | `PRIORITY_ICONS` | 🔴 high · 🟡 medium · 🟢 low |
| Task-type emojis | `task_icon()` | 🚶 walk · 🍖 feeding · ✂️ grooming · 🩺 vet · 🪥 brush · 📋 other (keyword match on the description) |
| Completion status | `print_schedule()` | ✅ done · ⬜ not done |

`main.py` also forces `sys.stdout.reconfigure(encoding="utf-8")` so the emoji and
box-drawing characters render on Windows consoles (which default to cp1252).

## 🧪 Testing

Actual output of `python -m pytest`:

```
..............                                                           [100%]
14 passed in 0.04s
```

The suite covers task completion, task addition (and pet-name tagging), sorting by
time, filtering by pet name, recurring task generation, one-off tasks not
recurring, conflict detection (including across pets), an empty-pet edge case,
priority-aware plan generation, the next-available-slot capability (including the
impossible-request case), and a JSON save/load round trip.

Confidence Level: ⭐⭐⭐⭐☆ (4/5) — core logic is well tested, but conflict
detection only checks exact time matches rather than overlapping durations.

## 📐 Scheduling Reference

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts by the HH:MM time string |
| Priority scheduling | `Scheduler.sort_by_priority_then_time()` | Priority first (`PRIORITY_ORDER`), then time |
| Filtering | `Scheduler.filter_tasks()` | By pet name, completion status, and/or frequency |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags same-time matches, including across different pets |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.process_completion()` | Daily/weekly tasks auto-generate via `timedelta` |
| Daily plan | `Scheduler.generate_plan()` | Fits tasks into a time budget, priority-first, with explanations |
| Next available slot | `Scheduler.find_next_available_slot()` | Earliest open gap that fits a given duration |
| Persistence | `Owner.save_to_json()` / `Owner.load_from_json()` | Custom dict conversion to/from `data.json` |

## 📸 Demo Walkthrough (Streamlit)

1. In the sidebar, add a pet (e.g. "Biscuit") using the Add a pet form.
2. Set your available minutes for the day using the preferences number input.
3. In the main panel, use the Schedule a task form to add a task — pick the pet, a description, time, duration, priority, and frequency (once/daily/weekly).
4. The Today's schedule table updates immediately, sorted by time. If two tasks land on the same time, a warning banner appears above the table.
5. Mark a task complete using the Mark a task complete dropdown. If it's a daily or weekly task, PawPal+ automatically schedules its next occurrence and shows a confirmation message.
6. Scroll to Generated daily plan to see which tasks fit in your time budget and which didn't, along with any conflict warnings.
