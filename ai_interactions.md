# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted.

---

## Agent Workflow (SF7)

> Documents using an AI coding agent (Claude Code) to make multi-step changes autonomously.

**Files modified**

- `pawpal_system.py` — added the `priority` field to `Task`; `to_dict()` /
  `from_dict()` on `Task`, `Pet`, and `Owner`; `Owner.save_to_json()` /
  `Owner.load_from_json()`; `Scheduler.sort_by_priority_then_time()`; and the new
  `Scheduler.find_next_available_slot()` (plus `_to_minutes` / `_to_hhmm` helpers).
- `main.py` — added the `tabulate` table renderer (`print_schedule`), emoji
  priority/type indicators, a priority-sorted schedule demo, and the persistence
  and next-available-slot demos; forced UTF-8 stdout.
- `tests/test_pawpal.py` — added tests for the next-available-slot capability
  (success + impossible case) and a JSON save/load round trip.
- `README.md` — added persistence workflow, priority-scheduling CLI examples, and
  the formatting-features documentation.

**What I asked the agent to do**

"Add a third algorithmic capability (next available slot), make data persist to a
`data.json` file, add Low/Medium/High priority scheduling, add professional CLI
formatting with tables and emojis, and document everything in the README and this
file."

**What the agent completed**

- Implemented all four capabilities above and wired them into the CLI demo.
- Restored the scheduler methods (`process_completion`, `generate_plan`) that had
  been left truncated mid-file, so the module imports and runs again.
- Ran `pytest` (14 passing) and executed `python main.py` to confirm real output
  before pasting it into the README.

**What I had to verify or fix manually**

- The agent's first `python main.py` run crashed with a `UnicodeEncodeError`
  because the Windows console defaults to cp1252 and can't print emoji. Fix:
  add `sys.stdout.reconfigure(encoding="utf-8")` at the top of `main.py`.
- Verified `find_next_available_slot()` against a hand-worked example (busy blocks
  at 08:00 → first 20-min gap is 08:30) rather than trusting the code blindly.
- Confirmed the JSON round trip preserves the `date` field, since that was the one
  non-primitive type that needed `isoformat()` / `fromisoformat()` handling.

---

## Prompt Comparison (SF11)

> Complex algorithmic task compared across two assistants: **the logic for
> rescheduling weekly recurring tasks** (given a completed weekly task, produce the
> next occurrence on the correct date).

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude (Claude Code) | Google Gemini |
| **Prompt** | "Given a Task with a `frequency` of daily/weekly and a `date`, write a method that returns the next occurrence with the correct future date. Keep it data-driven and easy to extend to new frequencies." | Same prompt |
| **Response summary** | Used a `RECURRING_FREQUENCIES = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}` lookup and returned a fresh `Task` with `date + RECURRING_FREQUENCIES[frequency]`, returning `None` for non-recurring tasks. | Hard-coded an `if frequency == "weekly": date + timedelta(days=7)` / `elif "daily"` branch and mutated the original task's `date` in place. |
| **What was useful** | Data-driven map makes adding a new frequency (e.g. "monthly") a one-line change; returning a new immutable-ish `Task` keeps the completed record intact. | Very readable and obvious for a beginner; the explicit branches were easy to follow. |
| **Problems noticed** | Slightly more abstract — a reader has to know what `RECURRING_FREQUENCIES` contains. | Mutating the original task's date loses the history of when it was completed, and the `if/elif` chain grows every time a new frequency is added; no clear handling of the `"once"` case (fell through to returning `None` only after I asked). |
| **Decision** | ✅ Chosen | Rejected |

**Which approach did you use in your final implementation and why?**

I used Claude's data-driven `RECURRING_FREQUENCIES` map (see `Task.next_occurrence()`
in `pawpal_system.py`). It keeps rescheduling logic in one dictionary instead of a
branching chain, returns a brand-new `Task` for the next date so the completed one
stays in the history (important for the recurring-task demo and tests), and cleanly
returns `None` for one-off tasks. Gemini's version was easier to read but its
in-place date mutation would have broken the "completed today, next occurrence
tomorrow" behavior that `test_recurrence_creates_next_day_task` checks.
