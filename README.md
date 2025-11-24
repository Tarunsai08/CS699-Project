Organ Donation Mapper

Organ Donation Mapper is a centralized web platform designed to facilitate the connection between medical institutions and patients in need of organ transplants. This application provides a secure environment for hospitals to manage donor records and enables patients to find compatible matches through a data-driven matching system that evaluates blood type, age, and organ viability.

Features

Role-Based Access Control: The system provides distinct portals for Administrators, Hospitals, and Users (Patients), ensuring secure and appropriate access to data.

Hospital Portal: Medical institutions can securely log in to batch import and parse donor data directly from CSV files.

Matching System: The application uses a specific algorithm to rank potential donors:

Blood Compatibility: It validates donor and recipient blood group compatibility (e.g., accounting for O- as a universal donor).

Age Tolerance: The system applies dynamic age windows depending on the specific organ required.

Viability Scoring: Matches are ranked by a composite score involving compatibility, age proximity, and the recency of the data.

Data Visualization: The platform generates dynamic charts (Bar, Line, Pie) to help users visualize match statistics and compatibility trends.

Admin Dashboard: A centralized interface for system administrators to manage hospital credentials and platform oversight.

Technical Stack

Backend: Python (Flask)

Database: MongoDB (via PyMongo)

Data Processing: Pandas (for CSV parsing and data cleaning)

Visualization: Matplotlib and Seaborn

Frontend: HTML5, CSS3, Jinja2 Templates

Security: Werkzeug (for password hashing and secure file handling)

Prerequisites

Before running the application, ensure you have the following installed:

Python 3.8 or higher

A MongoDB connection (either a local instance or a MongoDB Atlas URI)

Installation and Setup

Clone the repository
Download the project source code to your local machine.

git clone [https://github.com/yourusername/organ-donation-mapper.git](https://github.com/yourusername/organ-donation-mapper.git)
cd organ-donation-mapper


Create a Virtual Environment
It is recommended to run this project in a virtual environment to manage dependencies.

Windows:

python -m venv venv
venv\Scripts\activate


macOS/Linux:

python3 -m venv venv
source venv/bin/activate


Install Dependencies
Install the required Python packages listed in requirements.txt.

pip install -r requirements.txt


Configuration
Create a .env file in the root directory (or edit config.py directly) with your specific environment settings:

MONGODB_URI=mongodb+srv://dtarunsai08_db_user:WnZgLuK9MBsWKCeV@cluster0.o6yywhz.mongodb.net/?appName=Cluster0
DB_NAME="CS699"
SECRET_KEY=WnZgLuK9MBsWKCeV
UPLOAD_FOLDER=uploads
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
# WnZgLuK9MBsWKCeV


Run the Application
Start the Flask development server.

python app.py


You can now access the application at http://127.0.0.1:5000.

Usage Guide

Administrator

Login: Use the administrative credentials defined in your configuration file.

Role: The administrator is responsible for onboarding new medical institutions by registering Hospital accounts.

Hospital

Login: Use the credentials provided by the Administrator.

Role: Hospitals use the "Import Donor Data" feature to upload CSV files containing donor records.

Data Format: The system expects standard columns such as Age, Blood_Type, and Organ. The Serial No column is automatically ignored during the import process.

User (Patient)

Signup: Patients register by creating an account that includes their specific Age and Blood Group.

Search: Users can search for a target organ (e.g., Kidney, Liver).

Results: The system returns a ranked list of compatible donors, displaying viability scores and visual insights to aid decision-making.

Matching Logic Details

To ensure the most relevant results, the application ranks donors using a weighted scoring system:

Blood Type:

Exact matches receive the highest compatibility score (+150 points).

Compatible matches (based on medical standards) receive a secondary score (+100 points).

Age Proximity: The score is adjusted based on the age gap between the donor and the recipient; closer ages result in higher scores.

Data Freshness: Recently uploaded records are prioritized to ensure the viability of the donation data.

Project Structure

organ-donation-mapper/
├── app.py              # Main Flask application entry point
├── config.py           # Configuration settings
├── helpers.py          # Utilities for CSV parsing and admin creation
├── requirements.txt    # Python dependencies
├── static/             # CSS styles and images
├── templates/          # HTML templates (Jinja2)
└── uploads/            # Temporary storage for uploads and charts
