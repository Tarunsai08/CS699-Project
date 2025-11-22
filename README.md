# Organ Donation Mapper (Flask + MongoDB)

## Overview
Simple project to allow hospitals to upload donor CSVs and public users to search for matching donors. Donor rows are stored exactly as in the CSV (Serial No is ignored). Each donor record also stores `hospital_name` and `uploaded_at`.

Three roles:
- **admin** — manage hospital accounts (default admin/admin)
- **hospital** — login and upload CSV files (admin creates hospital accounts)
- **user** — public users who sign up and search donors

## Tech stack
- Python (Flask)
- MongoDB Atlas (pymongo)
- Pandas (CSV parsing)
- Matplotlib + Seaborn (visualizations)
- Plain HTML/CSS (templates in `templates/`)

## File structure
(see project root)

## How donor data is stored
- The `donors` collection stores only the CSV-provided columns for each uploaded CSV row.
- Two additional system fields are added:
  - `hospital_name` — hospital username that uploaded this CSV
  - `uploaded_at` — UTC timestamp of upload
- The application automatically **ignores** a `Serial No` column if present.

## Matching logic (brief)
- Primary filter: **Organ** matches exactly (case-insensitive).
- Optional filters: **Blood_Type** (exact), **Age** range (min/max).
- Simple scoring:
  - Exact blood-type match gets a high score bonus.
  - Age proximity to user's range center gives small bonus.
- Results are sorted by this simple score and returned to the user.
- Visualizations: age histogram, blood-group counts, matches-by-hospital pie chart.

## Setup & Run (local)
1. Clone the project:
   ```bash
   git clone <this-repo>
   cd organ-donation-mapper
