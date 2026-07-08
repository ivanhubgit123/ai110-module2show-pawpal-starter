"""
app.py

Streamlit UI for PawPal+. Wires the pawpal_system.py logic layer to a
browser-based interface. Uses st.session_state so the Owner instance
(and all its pets/tasks) persists across Streamlit's stateless reruns.
"""

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling")

# --- Session state setup -----------------------------------------------
# Streamlit reruns the whole script on every interaction, so without
# session_state our Owner would be wiped and recreated empty each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="My Household", preferences={"available_minutes": 60})

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner=owner)

# --- Sidebar: add a pet ---------------------------------------------------
st.sidebar.header("Add a pet")
with st.sidebar.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name")
    submitted_pet = st.form_submit_button("Add pet")
    if submitted_pet and new_pet_name.strip():
        owner.add_pet(Pet(name=new_pet_name.strip()))
        st.sidebar.success(f"Added {new_pet_name.strip()}!")

st.sidebar.divider()

# --- Sidebar: scheduling preferences --------------------------------------
st.sidebar.header("Preferences")
available_minutes = st.sidebar.number_input(
    "Available minutes today",
    min_value=0,
    max_value=1440,
    value=owner.preferences.get("available_minutes", 60),
    step=5,
)
owner.preferences["available_minutes"] = available_minutes

# --- Main: add a task ------------------------------------------------------
st.header("Schedule a task")

if not owner.get_all_pets():
    st.info("Add a pet from the sidebar first.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            pet_names = [p.name for p in owner.get_all_pets()]
            selected_pet_name = st.selectbox("Pet", pet_names)
            description = st.text_input("Task description (e.g. Morning walk)")
            time_str = st.text_input("Time (HH:MM)", value="08:00")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, value=15)
            priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=0)

        submitted_task = st.form_submit_button("Add task")
        if submitted_task and description.strip():
            pet = owner.get_pet_by_name(selected_pet_name)
            pet.add_task(
                Task(
                    description=description.strip(),
                    time=time_str,
                    duration=int(duration),
                    priority=priority,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{description.strip()}' for {selected_pet_name}.")

st.divider()

# --- Main: today's schedule ------------------------------------------------
st.header("Today's schedule")

all_tasks = scheduler.get_all_tasks()
sorted_tasks = scheduler.sort_by_time(all_tasks)

if not sorted_tasks:
    st.info("No tasks scheduled yet.")
else:
    table_rows = [
        {
            "Time": t.time,
            "Pet": t.pet_name,
            "Task": t.description,
            "Duration (min)": t.duration,
            "Priority": t.priority,
            "Frequency": t.frequency,
            "Completed": "✅" if t.completed else "⬜",
        }
        for t in sorted_tasks
    ]
    st.table(table_rows)

    # Conflict warnings, shown prominently so a pet owner can't miss them
    conflicts = scheduler.detect_conflicts(sorted_tasks)
    for warning in conflicts:
        st.warning(f"⚠️ {warning}")

    # Mark tasks complete
    st.subheader("Mark a task complete")
    task_labels = [f"{t.pet_name} — {t.description} ({t.time})" for t in sorted_tasks if not t.completed]
    if task_labels:
        selected_label = st.selectbox("Select a task", task_labels)
        if st.button("Mark complete"):
            index = task_labels.index(selected_label)
            incomplete_tasks = [t for t in sorted_tasks if not t.completed]
            task_to_complete = incomplete_tasks[index]
            next_task = scheduler.process_completion(task_to_complete)
            if next_task:
                st.success(
                    f"Marked complete! Since this task repeats {task_to_complete.frequency}, "
                    f"a new occurrence was scheduled for {next_task.date}."
                )
            else:
                st.success("Marked complete!")
            st.rerun()
    else:
        st.caption("All tasks are complete for now.")

st.divider()

# --- Main: generated daily plan ---------------------------------------------
st.header("Generated daily plan")
st.caption(f"Based on your {available_minutes}-minute time budget and task priorities.")

plan = scheduler.generate_plan(available_minutes=int(available_minutes))

if plan["scheduled"]:
    st.success(f"Plan uses {plan['minutes_used']} of {plan['minutes_available']} available minutes.")
    for t in plan["scheduled"]:
        st.write(f"✅ **{t.time}** — {t.pet_name}: {t.description} ({t.duration} min, {t.priority} priority)")
else:
    st.info("No tasks fit in today's time budget yet.")

if plan["skipped"]:
    st.warning("Some tasks didn't fit in today's schedule:")
    for t in plan["skipped"]:
        st.write(f"⬜ {t.pet_name}: {t.description} ({t.duration} min, {t.priority} priority)")

for conflict in plan["conflicts"]:
    st.error(f"⚠️ {conflict}")