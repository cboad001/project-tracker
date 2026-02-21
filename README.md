# Company Project Tracker

A user-friendly project intake tracker for company teams.

## Features
- Add new projects with client, owner, status, priority, dates, budget, and notes
- Search by project/client/owner
- Filter by status and priority
- Edit or delete existing projects
- Local SQLite database (`projects.db`) for simple setup

## Run
1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Start the app:
   ```powershell
   streamlit run app.py
   ```
3. Open the local URL shown by Streamlit (usually `http://localhost:8501`).

## Database
The app automatically creates `projects.db` and the `projects` table on first run.
# project-tracker
