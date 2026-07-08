"""
tests/test_pawpal.py

Automated test suite for PawPal+ core logic. Covers task completion,
task addition, sorting, recurring tasks, and conflict detection.
"""

from datetime import date, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_complete_changes_status():
    """Task Completion: calling mark_complete() should flip completed to True."""
    task = Task(description="Walk", time="08:00", duration=30)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should increase its task count."""
    pet = Pet(name="Biscuit")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(description="Feeding", time="08:00", duration=10))
    assert len(pet.get_tasks()) == 1


def test_add_task_sets_pet_name():
    """Adding a task to a pet should automatically tag it with the pet's name."""
    pet = Pet(name="Mochi")
    task = Task(description="Grooming", time="09:00", duration=40)
    pet.add_task(task)
    assert task.pet_name == "Mochi"


def test_sort_by_time_returns_chronological_order():
    """Sorting Correctness: tasks should come back in chronological order."""
    owner = Owner(name="Alex")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task(description="Evening walk", time="18:00", duration=30))
    pet.add_task(Task(description="Morning walk", time="08:00", duration=30))
    pet.add_task(Task(description="Midday feeding", time="12:00", duration=10))

    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_time(scheduler.get_all_tasks())
    times = [t.time for t in sorted_tasks]
    assert times == ["08:00", "12:00", "18:00"]


def test_filter_tasks_by_pet_name():
    owner = Owner(name="Alex")
    biscuit = Pet(name="Biscuit")
    mochi = Pet(name="Mochi")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    biscuit.add_task(Task(description="Walk", time="08:00", duration=30))
    mochi.add_task(Task(description="Grooming", time="09:00", duration=40))

    scheduler = Scheduler(owner=owner)
    biscuit_tasks = scheduler.filter_tasks(pet_name="Biscuit")
    assert len(biscuit_tasks) == 1
    assert biscuit_tasks[0].pet_name == "Biscuit"


def test_recurrence_creates_next_day_task():
    """Recurrence Logic: completing a daily task should create a task for tomorrow."""
    owner = Owner(name="Alex")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    task = Task(description="Walk", time="08:00", duration=30, frequency="daily")
    pet.add_task(task)

    scheduler = Scheduler(owner=owner)
    next_task = scheduler.process_completion(task)

    assert task.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.date == task.date + timedelta(days=1)
    assert len(pet.get_tasks()) == 2


def test_one_off_task_does_not_recur():
    """A task with frequency='once' should not generate a next occurrence."""
    owner = Owner(name="Alex")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    task = Task(description="Vet visit", time="10:00", duration=60, frequency="once")
    pet.add_task(task)

    scheduler = Scheduler(owner=owner)
    next_task = scheduler.process_completion(task)

    assert next_task is None
    assert len(pet.get_tasks()) == 1


def test_conflict_detection_flags_duplicate_times():
    """Conflict Detection: two tasks at the same time on the same day should be flagged."""
    owner = Owner(name="Alex")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task(description="Walk", time="08:00", duration=30))
    pet.add_task(Task(description="Feeding", time="08:00", duration=10))

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts(scheduler.get_all_tasks())
    assert len(conflicts) == 1


def test_no_conflict_for_different_times():
    owner = Owner(name="Alex")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task(description="Walk", time="08:00", duration=30))
    pet.add_task(Task(description="Evening walk", time="18:00", duration=30))

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts(scheduler.get_all_tasks())
    assert conflicts == []


def test_pet_with_no_tasks():
    """Edge case: a pet with no tasks should not break sorting or filtering."""
    owner = Owner(name="Alex")
    pet = Pet(name="Ghost")
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    assert scheduler.get_all_tasks() == []
    assert scheduler.sort_by_time([]) == []
    assert scheduler.detect_conflicts([]) == []


def test_generate_plan_respects_time_budget_and_priority():
    owner = Owner(name="Alex")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task(description="Walk", time="08:00", duration=30, priority="high"))
    pet.add_task(Task(description="Grooming", time="09:00", duration=40, priority="low"))

    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_plan(available_minutes=35)

    assert plan["minutes_used"] == 30
    assert len(plan["scheduled"]) == 1
    assert plan["scheduled"][0].description == "Walk"
    assert len(plan["skipped"]) == 1
    assert plan["skipped"][0].description == "Grooming"