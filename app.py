from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from db import add_project, delete_project, get_project, init_db, list_projects, update_project

STATUS_OPTIONS = ["New", "In Progress", "On Hold", "Completed", "Cancelled"]
PRIORITY_OPTIONS = ["Low", "Medium", "High", "Urgent"]


st.set_page_config(page_title="Project Tracker", layout="wide")
init_db()
LOGO_PATH = Path("assets/logo.svg")

if "success_message" not in st.session_state:
    st.session_state.success_message = None
if "pending_bulk_delete_ids" not in st.session_state:
    st.session_state.pending_bulk_delete_ids = []

st.markdown(
    """
    <style>
    :root {
        --primary: #3b82f6;
        --primary-strong: #2563eb;
        --bg-main: #f4f8ff;
        --bg-elev: #ffffff;
        --bg-soft: #eaf2ff;
        --border: #c8d9f8;
        --text-main: #0f172a;
        --text-dim: #475569;
    }

    .stApp {
        background: linear-gradient(180deg, #f7fbff 0%, #eef5ff 45%, #e6f0ff 100%);
        color: var(--text-main);
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
    }

    h1, h2, h3, p, label, span, div {
        color: var(--text-main);
    }

    [data-testid="stSidebar"] {
        background: #eaf2ff;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--text-main);
    }

    div[data-testid="stForm"] {
        background: var(--bg-soft);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem 1.2rem;
    }

    .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
        background: var(--primary);
        color: #ffffff;
        border: 1px solid var(--primary);
        border-radius: 10px;
        font-weight: 700;
    }

    .stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background: var(--primary-strong);
        border-color: var(--primary-strong);
        color: #ffffff;
    }

    div[data-baseweb="select"] > div, .stTextInput > div > div > input, .stTextArea textarea, .stNumberInput input {
        border-radius: 10px;
        border: 1px solid var(--border);
        background: var(--bg-elev);
        color: var(--text-main);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
    }

    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="columnheader"] {
        font-size: 1.02rem;
    }

    [data-testid="stInfo"], [data-testid="stSuccess"], [data-testid="stWarning"], [data-testid="stError"] {
        border-radius: 10px;
        border: 1px solid var(--border);
        background: var(--bg-soft);
        color: var(--text-main);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

header_left, header_right = st.columns([0.1, 0.9], gap="small")
with header_left:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=72)
with header_right:
    st.title("Project Tracker")
    st.caption("Track every incoming project in one place.")

if st.session_state.success_message:
    st.success(st.session_state.success_message)
    st.session_state.success_message = None


with st.sidebar:
    st.header("Filter Projects")
    search = st.text_input("Search", placeholder="Project, client, or owner").strip()
    status_filter = st.selectbox("Status", ["All", *STATUS_OPTIONS])
    priority_filter = st.selectbox("Priority", ["All", *PRIORITY_OPTIONS])

rows = list_projects(search=search, status=status_filter, priority=priority_filter)

left, right = st.columns([1.1, 1.9], gap="large")

if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "pending_delete_id" not in st.session_state:
    st.session_state.pending_delete_id = None

with left:
    st.subheader("Add Project")
    button_label = "Hide Add Form" if st.session_state.show_add_form else "Add Project"
    if st.button(button_label, use_container_width=True):
        st.session_state.show_add_form = not st.session_state.show_add_form
        st.rerun()

    if st.session_state.show_add_form:
        with st.form("create_project", clear_on_submit=True):
            project_name = st.text_input("Project Name*")
            client_name = st.text_input("Client Name*")
            owner = st.text_input("Project Owner*")
            status = st.selectbox("Status", STATUS_OPTIONS, index=0)
            priority = st.selectbox("Priority", PRIORITY_OPTIONS, index=1)
            intake_date = st.date_input("Intake Date", value=date.today())
            has_due_date = st.checkbox("Set due date", value=False)
            due_date = st.date_input("Due Date", value=date.today(), disabled=not has_due_date)
            budget = st.number_input("Budget (GHS)", min_value=0.0, step=100.0, value=0.0, format="%.2f")
            notes = st.text_area("Notes", placeholder="Scope, key contacts, special requirements...")

            submitted = st.form_submit_button("Save Project")
            if submitted:
                if not project_name.strip() or not client_name.strip() or not owner.strip():
                    st.error("Project Name, Client Name, and Project Owner are required.")
                else:
                    add_project(
                        {
                            "project_name": project_name.strip(),
                            "client_name": client_name.strip(),
                            "owner": owner.strip(),
                            "status": status,
                            "priority": priority,
                            "intake_date": str(intake_date),
                            "due_date": str(due_date) if has_due_date else None,
                            "budget": float(budget),
                            "notes": notes.strip() if notes.strip() else None,
                        }
                    )
                    st.session_state.success_message = "Project added successfully."
                    st.session_state.show_add_form = False
                    st.rerun()

with right:
    st.subheader("Project List")
    if not rows:
        st.info("No projects found. Add your first project on the left.")
    else:
        df = pd.DataFrame(rows, columns=rows[0].keys())
        df = df.sort_values(by="id", ascending=True)
        display_cols = [
            "id",
            "project_name",
            "client_name",
            "owner",
            "status",
            "priority",
            "intake_date",
            "due_date",
            "budget",
            "updated_at",
        ]
        df["budget"] = df["budget"].apply(lambda v: f"GHS {v:,.2f}" if pd.notnull(v) else "")
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        ids = df["id"].tolist()
        ids_to_delete = st.multiselect("Select Projects to Delete", ids)
        if st.button("Delete Selected Projects", type="secondary", use_container_width=True):
            if not ids_to_delete:
                st.warning("Select at least one project to delete.")
            else:
                st.session_state.pending_bulk_delete_ids = [int(project_id) for project_id in ids_to_delete]
                st.rerun()

        if st.session_state.pending_bulk_delete_ids:
            bulk_count = len(st.session_state.pending_bulk_delete_ids)
            bulk_target = "this project" if bulk_count == 1 else "these projects"
            st.warning(f"Are you sure you want to delete {bulk_target}?")
            bulk_confirm_col, bulk_cancel_col = st.columns(2)
            if bulk_confirm_col.button("Yes, Delete Selected", type="primary", use_container_width=True):
                deleted_count = len(st.session_state.pending_bulk_delete_ids)
                for project_id in st.session_state.pending_bulk_delete_ids:
                    delete_project(int(project_id))
                st.session_state.pending_bulk_delete_ids = []
                st.session_state.success_message = f"Deleted {deleted_count} project(s) successfully."
                st.rerun()
            if bulk_cancel_col.button("Cancel Bulk Delete", use_container_width=True):
                st.session_state.pending_bulk_delete_ids = []
                st.rerun()

        selected_id = st.selectbox("Select Project to Edit/Delete", ids)
        project = get_project(int(selected_id))

        if project:
            with st.expander("Edit Selected Project", expanded=False):
                with st.form("edit_project"):
                    project_name = st.text_input("Project Name*", value=project["project_name"])
                    client_name = st.text_input("Client Name*", value=project["client_name"])
                    owner = st.text_input("Project Owner*", value=project["owner"])
                    status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(project["status"]))
                    priority = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(project["priority"]))
                    intake_date = st.date_input("Intake Date", value=date.fromisoformat(project["intake_date"]))
                    existing_due = date.fromisoformat(project["due_date"]) if project["due_date"] else date.today()
                    has_due_date = st.checkbox("Set due date", value=project["due_date"] is not None, key="edit_has_due")
                    due_date = st.date_input("Due Date", value=existing_due, disabled=not has_due_date, key="edit_due")
                    budget_value = float(project["budget"]) if project["budget"] is not None else 0.0
                    budget = st.number_input("Budget (GHS)", min_value=0.0, step=100.0, value=budget_value, format="%.2f")
                    notes = st.text_area("Notes", value=project["notes"] or "")

                    c1, c2 = st.columns(2)
                    do_update = c1.form_submit_button("Update Project")
                    do_delete = c2.form_submit_button("Delete Project", type="secondary")

                    if do_update:
                        if not project_name.strip() or not client_name.strip() or not owner.strip():
                            st.error("Project Name, Client Name, and Project Owner are required.")
                        else:
                            update_project(
                                int(selected_id),
                                {
                                    "project_name": project_name.strip(),
                                    "client_name": client_name.strip(),
                                    "owner": owner.strip(),
                                    "status": status,
                                    "priority": priority,
                                    "intake_date": str(intake_date),
                                    "due_date": str(due_date) if has_due_date else None,
                                    "budget": float(budget),
                                    "notes": notes.strip() if notes.strip() else None,
                                },
                            )
                            st.session_state.success_message = "Project updated successfully."
                            st.rerun()

                    if do_delete:
                        st.session_state.pending_delete_id = int(selected_id)
                        st.rerun()

            if st.session_state.pending_delete_id == int(selected_id):
                st.warning("Are you sure you want to delete this project?")
                confirm_col, cancel_col = st.columns(2)
                if confirm_col.button("Yes, Delete", type="primary", use_container_width=True):
                    delete_project(int(selected_id))
                    st.session_state.pending_delete_id = None
                    st.session_state.success_message = "Project deleted successfully."
                    st.rerun()
                if cancel_col.button("Cancel", use_container_width=True):
                    st.session_state.pending_delete_id = None
                    st.rerun()
