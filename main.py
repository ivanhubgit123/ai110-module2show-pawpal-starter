"""
main.py

CLI demo script for PawPal+. Verifies that the backend logic in
pawpal_system.py works correctly before wiring it up to the Streamlit UI.
"""

import sys

from tabulate import tabulate

from pawpal_system import Owner, Pet, Task, Scheduler

# Emojis/box-drawing require UTF-8; Windows consoles default to cp1252, so force it.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PRIORITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}
TASK_TYPE_ICONS = {
    "walk": "🚶", "feeding": "🍖", "grooming": "✂️", "vet": "🩺", "brush": "🪥",
}


def task_icon(description: str) -> str:
    """Pick an emoji based on keywords in the task description, defaulting to a generic icon."""
    lower_desc = description.lower()
    for keyword, icon in TASK_TYPE_ICONS.items():
        if keyword in lower_desc:
            return icon
    return "📋"


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print a formatted table of tasks using tabulate, with emoji priority/type indicators."""
    print(f"\n{title}")
    print("=" * len(title))
    if not tasks:
        print("  (no tasks)")
        return

    rows = [
        [
            "✅" if task.completed else "⬜",
            task_icon(task.description),
            task.time,
            task.pet_name,
            task.description,
            f"{task.duration} min",
            f"{PRIORITY_ICONS.get(task.priority, '')} {task.priority}",
            task.frequency,
        ]
        for task in tasks
    ]
    headers = ["Done", "Type", "Time", "Pet", "Task", "Duration", "Priority", "Frequency"]
    print(tabulate(rows, headers=headers, tablefmt="simple"))


def main():
    # 1. Create an owner and two pets
    owner = Owner(name="Alex", preferences={"available_minutes": 60})
    biscuit = Pet(name="Biscuit")
    mochi = Pet(name="Mochi")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # 2. Add tasks out of order, including a recurring task and a conflict
    biscuit.add_task(Task(description="Morning walk", time="08:00", duration=30, priority="high", frequency="daily"))
    biscuit.add_task(Task(description="Feeding", time="08:00", duration=10, priority="high"))
    mochi.add_task(Task(description="Grooming", time="09:00", duration=40, priority="low"))
    mochi.add_task(Task(description="Evening feeding", time="18:00", duration=10, priority="medium"))
    mochi.add_task(Task(description="Morning brush", time="08:00", duration=15, priority="medium"))

    scheduler = Scheduler(owner=owner)

    # 3. Today's full schedule, sorted by time
    all_tasks = scheduler.get_all_tasks()
    sorted_tasks = scheduler.sort_by_time(all_tasks)
    print_schedule("Today's Schedule (sorted by time)", sorted_tasks)

    # 3b. Same tasks re-ordered by priority first, then time within each priority
    priority_sorted = scheduler.sort_by_priority_then_time(all_tasks)
    print_schedule("Today's Schedule (sorted by priority, then time)", priority_sorted)

    # 4. Filtering example
    high_priority = [t for t in all_tasks if t.priority == "high"]
    print_schedule("High Priority Tasks", high_priority)

    # 4b. Filtering using Scheduler.filter_tasks() directly
    biscuits_tasks = scheduler.filter_tasks(pet_name="Biscuit")
    print_schedule("Biscuit's Tasks (via filter_tasks)", biscuits_tasks)

    incomplete_tasks = scheduler.filter_tasks(completed=False)
    print_schedule("Incomplete Tasks (via filter_tasks)", incomplete_tasks)

    # 5. Conflict detection
    conflicts = scheduler.detect_conflicts(all_tasks)
    print("\nConflict Check")
    print("-" * len("Conflict Check"))
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts found.")

    # 6. Generate today's plan with explanations
    plan = scheduler.generate_plan(available_minutes=owner.preferences["available_minutes"])
    print("\nGenerated Daily Plan")
    print("-" * len("Generated Daily Plan"))
    print(f"  Time budget: {plan['minutes_used']} / {plan['minutes_available']} minutes used")
    for line in plan["explanation"]:
        print(f"  - {line}")

    # 7. Recurring task demo: complete the daily walk and show the next occurrence
    walk = next(t for t in biscuit.tasks if t.description == "Morning walk")
    next_task = scheduler.process_completion(walk)
    print("\nRecurring Task Demo")
    print("-" * len("Recurring Task Demo"))
    print(f"  Marked '{walk.description}' complete for {walk.date}.")
    if next_task:
        print(f"  Automatically scheduled next occurrence for {next_task.date} at {next_task.time}.")

    # 8. Data persistence demo: save to JSON, then reload into a fresh Owner
    owner.save_to_json("data.json")
    print("\nData Persistence Demo")
    print("-" * len("Data Persistence Demo"))
    print("  Saved current owner, pets, and tasks to data.json.")
    reloaded_owner = Owner.load_from_json("data.json")
    reloaded_scheduler = Scheduler(owner=reloaded_owner)
    print(f"  Reloaded owner '{reloaded_owner.name}' with {len(reloaded_owner.get_all_pets())} pets "
          f"and {len(reloaded_scheduler.get_all_tasks())} total tasks.")

    # 9. Advanced capability demo: find the next available 20-minute slot
    slot = scheduler.find_next_available_slot(duration_minutes=20)
    print("\nNext Available Slot Demo")
    print("-" * len("Next Available Slot Demo"))
    if slot:
        print(f"  Next available 20-minute slot today: {slot}")
    else:
        print("  No available 20-minute slot found today.")


if __name__ == "__main__":
    main()