"""
pawpal_system.py

Logic layer for PawPal+. Contains the core backend classes:
Task, Pet, Owner, and Scheduler.

Implements: sorting, filtering, conflict detection, recurring tasks,
and priority-aware daily plan generation with explanations.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
import json

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
        """Return the next occurrence if this task recurs, else None."""
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

    def to_dict(self) -> dict:
        """Convert this task to a JSON-serializable dictionary."""
        return {
            "description": self.description,
            "time": self.time,
            "duration": self.duration,
            "frequency": self.frequency,
            "priority": self.priority,
            "pet_name": self.pet_name,
            "date": self.date.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a dictionary (e.g. loaded from JSON)."""
        return cls(
            description=data["description"],
            time=data["time"],
            duration=data["duration"],
            frequency=data.get("frequency", "once"),
            priority=data.get("priority", "medium"),
            pet_name=data.get("pet_name", ""),
            date=date.fromisoformat(data["date"]),
            completed=data.get("completed", False),
        )


@dataclass
class Pet:
    """A pet belonging to an Owner, with its own list of tasks."""

    name: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def to_dict(self) -> dict:
        """Convert this pet (and its tasks) to a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Reconstruct a Pet (and its tasks) from a dictionary."""
        return cls(
            name=data["name"],
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
        )


@dataclass
class Owner:
    """A pet owner who manages one or more pets and has scheduling preferences."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)  # e.g. preferred time windows, priorities

    def add_pet(self, pet: Pet) -> None:
        """Add a new pet to this owner's list."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's list."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_all_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_pet_by_name(self, name: str) -> Pet | None:
        """Look up a pet by name, or return None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def to_dict(self) -> dict:
        """Convert this owner (and all pets/tasks) to a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "preferences": self.preferences,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Reconstruct an Owner (and all pets/tasks) from a dictionary."""
        return cls(
            name=data["name"],
            preferences=data.get("preferences", {}),
            pets=[Pet.from_dict(p) for p in data.get("pets", [])],
        )

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Save this owner and all pets/tasks to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> "Owner":
        """Load an owner and all pets/tasks from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class Scheduler:
    """The 'brain' that retrieves, organizes, and plans tasks across an owner's pets."""

    owner: Owner

    def get_all_tasks(self) -> list[Task]:
        """Collect all tasks across all of the owner's pets."""
        all_tasks: list[Task] = []
        for pet in self.owner.get_all_pets():
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted chronologically by time."""
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority_then_time(self, tasks: list[Task]) -> list[Task]:
        """Advanced scheduling: sort by priority (high first), then by time within each priority."""
        return sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.priority, 1), t.time))

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        frequency: str | None = None,
    ) -> list[Task]:
        """Return tasks filtered by pet name, status, and/or frequency."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if frequency is not None:
            tasks = [t for t in tasks if t.frequency == frequency]
        return tasks

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warnings for tasks scheduled at the same time."""
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
        """Mark a task complete and auto-schedule its next occurrence if recurring."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet = self.owner.get_pet_by_name(task.pet_name)
            if pet is not None:
                pet.add_task(next_task)
        return next_task

    def generate_plan(self, available_minutes: int) -> dict:
        """Build a priority-based daily plan that fits the time budget, with explanations."""
        tasks = self.sort_by_priority_then_time(self.filter_tasks(completed=False))

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

    @staticmethod
    def _to_minutes(hhmm: str) -> int:
        """Convert a 'HH:MM' string to minutes since midnight."""
        hours, minutes = hhmm.split(":")
        return int(hours) * 60 + int(minutes)

    @staticmethod
    def _to_hhmm(total_minutes: int) -> str:
        """Convert minutes since midnight back to a zero-padded 'HH:MM' string."""
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    def find_next_available_slot(
        self,
        duration_minutes: int,
        day_start: str = "08:00",
        day_end: str = "22:00",
        on_date: date | None = None,
    ) -> str | None:
        """Third algorithmic capability: find the earliest open slot today that fits a task.

        Walks the day's existing tasks in chronological order and returns the first
        gap (as 'HH:MM') large enough to hold ``duration_minutes``, or None if the day
        has no room. Existing tasks are treated as busy intervals [start, start+duration).
        """
        if on_date is None:
            on_date = date.today()

        start = self._to_minutes(day_start)
        end = self._to_minutes(day_end)

        busy = sorted(
            (self._to_minutes(t.time), self._to_minutes(t.time) + t.duration)
            for t in self.get_all_tasks()
            if t.date == on_date
        )

        cursor = start
        for busy_start, busy_end in busy:
            if busy_start - cursor >= duration_minutes:
                return self._to_hhmm(cursor)
            cursor = max(cursor, busy_end)

        if end - cursor >= duration_minutes:
            return self._to_hhmm(cursor)
        return None