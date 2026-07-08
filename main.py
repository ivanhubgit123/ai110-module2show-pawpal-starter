"""
main.py

CLI demo script for PawPal+. Verifies that the backend logic in
pawpal_system.py works correctly before wiring it up to the Streamlit UI.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print a readable, formatted list of tasks."""
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("  (no tasks)")
        return
    for task in tasks:
        status = "[x]" if task.completed else "[ ]"
        print(
            f"  {status} {task.time}  {task.pet_name:<10} {task.description:<20} "
            f"({task.duration} min, priority: {task.priority}, {task.frequency})"
        )


def main():
    owner = Owner(name="Alex", preferences={"available_minutes": 60})
    biscuit = Pet(name="Biscuit")
    mochi = Pet(name="Mochi")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    biscuit.add_task(Task(description="Morning walk", time="08:00", duration=30, priority="high", frequency="daily"))
    biscuit.add_task(Task(description="Feeding", time="08:00", duration=10, priority="high"))
    mochi.add_task(Task(description="Grooming", time="09:00", duration=40, priority="low"))
    mochi.add_task(Task(description="Evening feeding", time="18:00", duration=10, priority="medium"))
    mochi.add_task(Task(description="Morning brush", time="08:00", duration=15, priority="medium"))

    scheduler = Scheduler(owner=owner)

    all_tasks = scheduler.get_all_tasks()
    sorted_tasks = scheduler.sort_by_time(all_tasks)
    print_schedule("Today's Schedule", sorted_tasks)

    high_priority = [t for t in all_tasks if t.priority == "high"]
    print_schedule("High Priority Tasks", high_priority)

    biscuits_tasks = scheduler.filter_tasks(pet_name="Biscuit")
    print_schedule("Biscuit's Tasks (via filter_tasks)", biscuits_tasks)

    incomplete_tasks = scheduler.filter_tasks(completed=False)
    print_schedule("Incomplete Tasks (via filter_tasks)", incomplete_tasks)

    conflicts = scheduler.detect_conflicts(all_tasks)
    print("\nConflict Check")
    print("-" * len("Conflict Check"))
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts found.")

    plan = scheduler.generate_plan(available_minutes=owner.preferences["available_minutes"])
    print("\nGenerated Daily Plan")
    print("-" * len("Generated Daily Plan"))
    print(f"  Time budget: {plan['minutes_used']} / {plan['minutes_available']} minutes used")
    for line in plan["explanation"]:
        print(f"  - {line}")

    walk = next(t for t in biscuit.tasks if t.description == "Morning walk")
    next_task = scheduler.process_completion(walk)
    print("\nRecurring Task Demo")
    print("-" * len("Recurring Task Demo"))
    print(f"  Marked '{walk.description}' complete for {walk.date}.")
    if next_task:
        print(f"  Automatically scheduled next occurrence for {next_task.date} at {next_task.time}.")


if __name__ == "__main__":
    main()
