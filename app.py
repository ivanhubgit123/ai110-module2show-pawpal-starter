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
            duration = st.number_input("Duration (minutes)",