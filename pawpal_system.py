"""
pawpal_system.py

Logic layer for PawPal+. Contains the core backend classes:
Task, Pet, Owner, and Scheduler.

Implements: sorting, filtering, conflict detection, recurring tasks,
and priority-aware daily plan generation with explanations.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
RECURRING_FREQUENCIES = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


@dataclass
class Task:
    """A single activity to be done for a pet (e.g. a walk or a feeding)."""

    description: str
    time: str  # "HH:MM" format
    duration: int  # duration in minutes
    frequency: str = "once"  # "once", "daily", or "weekly"
    priority: str = "medium"  # "low", "medium", or "high"
    pet_name: str = ""  # which pet this task belongs to, for plan explanations
    date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """
        If this task is recurring (daily/weekly), return a fresh Task
        representing the next occurrence. Returns None for one-off tasks.
        """
        if self.frequency not in RECURRING_FREQUENCIES:
            return None
        return Task(
            description=self.description,
            time=self.time,
            duration=self.duration,
            frequency=self.frequency,
            priority=self.priority,
            pet_name=self.pet_name,
            date=self.date + RECURRING_FREQUENCIES[self.frequency],
            completed=False,
        )


@dataclass
class Pet:
    """A pet belonging to an Owner, with its own list of tasks."""

    name: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new task to this pet's task list and tag it with this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return self.tasks


@dataclass
class Owner:
    """A pet owner who manages one or more pets and has scheduling preferences."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)  # e.g. preferred time windows, priorities

    def add_pet(self, pet: Pet) -> None:
        """Add a new pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's list of pets."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_all_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_pet_by_name(self, name: str) -> Pet | None:
        """Look up a pet by name. Returns None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None


@dataclass
class Scheduler:
    """The 'brain' that retrieves, organizes, and plans tasks across an owner's pets."""

    owner: Owner

    def get_all_tasks(self) -> list[Task]:
        """
        Collect all tasks across all of the owner's pets.

        Talks to Owner via get_all_pets(), then asks each Pet for its own
        tasks via get_tasks() rather than reaching into Pet.tasks directly.
        """
        all_tasks: list[Task] = []
        for pet in self.owner.get_all_pets():
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted chronologically by their time attribute ("HH:MM")."""
        return sorted(tasks, key=lambda t: t.time)

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        frequency: str | None = None,
    ) -> list[Task]:
        """Return tasks filtered by pet name, completion status, and/or frequency."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if frequency is not None:
            tasks = [t for t in tasks if t.frequency == frequency]
        return tasks

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """
        Return warning messages for any tasks scheduled at the same time
        on the same date. This is a lightweight check (exact time match
        only) rather than true overlapping-duration detection.
        """
        warnings: list[str] = []
        seen: dict[tuple, list[Task]] = {}
        for task in tasks:
            key = (task.date, task.time)
            seen.setdefault(key, []).append(task)

        for (task_date, time), tasks_at_time in seen.items():
            if len(tasks_at_time) > 1:
                names = ", ".join(f"{t.pet_name}: {t.description}" for t in tasks_at_time)
                warnings.append(f"Conflict on {task_date} at {time} — {names}")
        return warnings

    def process_completion(self, task: Task) -> Task | None:
        """
        Mark a task complete, and if it's recurring, automatically create
        and attach the next occurrence to the same pet. Returns the new
        Task if one was created, otherwise None.
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet = self.owner.get_pet_by_name(task.pet_name)
            if pet is not None:
                pet.add_task(next_task)
        return next_task

    def generate_plan(self, available_minutes: int) -> dict:
        """
        Build a daily plan that fits within available_minutes, respecting
        task priority and the owner's preferences. Returns a plan along
        with a brief explanation of why each task was included or skipped.

        Strategy: sort incomplete tasks by priority (high first), then by
        time, and greedily include tasks until the time budget runs out.
        """
        tasks = self.filter_tasks(completed=False)
        tasks = sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.priority, 1), t.time))

        scheduled: list[Task] = []
        skipped: list[Task] = []
        minutes_used = 0

        for task in tasks:
            if minutes_used + task.duration <= available_minutes:
                scheduled.append(task)
                minutes_used += task.duration
            else:
                skipped.append(task)

        conflicts = self.detect_conflicts(scheduled)

        explanation = []
        for task in scheduled:
            explanation.append(
                f"Included {task.pet_name}'s '{task.description}' at {task.time} "
                f"(priority: {task.priority}, {task.duration} min)."
            )
        for task in skipped:
            explanation.append(
                f"Skipped {task.pet_name}'s '{task.description}' — not enough time remaining "
                f"(priority: {task.priority}, {task.duration} min)."
            )
        for conflict in conflicts:
            explanation.append(f"Warning: {conflict}")

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "conflicts": conflicts,
            "minutes_used": minutes_used,
            "minutes_available": available_minutes,
            "explanation": explanation,
        }