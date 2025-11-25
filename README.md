# **Organ Donation Mapper**

Organ Donation Mapper is a centralized web platform designed to facilitate the connection between medical institutions and patients in need of organ transplants. This application provides a secure environment for hospitals to manage donor records and enables patients to find compatible matches through a data-driven matching system that evaluates blood type, age, and organ viability.

## **Features**

* **Role-Based Access Control:** Distinct portals for Administrators, Hospitals, and Users (Patients).  
* **Hospital Portal:** Secure login for medical institutions to batch import donor data via CSV.  
* **Intelligent Matching Algorithm:**  
  * **Blood Compatibility:** Checks donor/recipient compatibility (e.g., O- as universal donor).  
  * **Age Tolerance:** Varies match windows based on the specific organ required.  
  * **Viability Scoring:** Ranks matches by compatibility, age proximity, and data freshness.  
* **Data Visualization:** Generates dynamic charts (Bar, Line, Pie) for match statistics.  
* **Admin Dashboard:** Centralized management for hospital credentialing.
* **Automatic Donor Allocation:** Once approved, system picks best donor using same scoring logic as search.
* **Donor Locking:** Allocated donors are hidden from search/hospital dashboards.
* **User Request Tracking:** Users can see matched donor name + hospital name.
* **Admin Request Panel:** Admin can approve or reject a Request raised by users.

## **Technical Stack**

* **Backend:** Python (Flask)  
* **Database:** MongoDB (via PyMongo)  
* **Data Processing:** Pandas (CSV parsing)  
* **Visualization:** Matplotlib, Seaborn  
* **Frontend:** HTML5, CSS3, Jinja2 Templates  
* **Security:** Werkzeug (Password hashing)

## **Prerequisites**

* Python 3.8 or higher  
* A MongoDB connection (Local or Atlas URI)

## **Installation and Setup**

**1\. Clone the repository**  
git clone  https://github.com/Tarunsai08/CS699-Project  
cd CS699-Project  
**2\. Create a Virtual Environment**  
Windows:  
python \-m venv venv  
venv\\Scripts\\activate

macOS/Linux:  
python3 \-m venv venv  
source venv/bin/activate

**3\. Install Dependencies**  
pip install \-r requirements.txt

**4\. Configuration**

**MONGODB\_URI=mongodb+srv://dtarunsai08\_db\_user:WnZgLuK9MBsWKCeV@cluster0.o6yywhz.mongodb.net/?appName=Cluster0**  
**DB\_NAME="CS699"**  
**SECRET\_KEY=WnZgLuK9MBsWKCeV**  
**UPLOAD\_FOLDER=uploads**  
**ADMIN\_USERNAME=admin**  
**ADMIN\_PASSWORD=admin**  

**5\. Run the Application**  
python app.py

Access the app at http://127.0.0.1:5000.

## **Usage Guide**

### **Administrator**

* **Login:** Use the credentials from your config file.  
* **Role:** Register new Hospital accounts.
* **Approve Requests:** Approve or Reject the Requests made by the user.

### **Hospital**

* **Login:** Use credentials provided by the Admin.  
* **Role:** Upload CSV files containing donor records.  
* **Note:** The Serial No column in CSVs is automatically ignored.

### **User (Patient)**

* **Signup:** Register with your Age and Blood Group.  
* **Search:** Enter a target organ (e.g., Kidney) to see ranked matches.
* **Request:** Raise a Request for the Target organ required

## **Project Structure**

```
organ-donation-mapper/
├── app.py
├── config.py
├── helpers.py
├── requirements.txt
├── static/
│   └── css/styles.css
├── templates/
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── edit_hospital.html
│   │   ├── requests.html
│   ├── hospital/
│   │   ├── dashboard.html
│   │   ├── upload.html
│   │   ├── edit_donor.html
│   ├── user/
│   │   ├── request_organ.html
│   │   ├── my_requests.html
│   ├── results.html
│   ├── search.html
│   ├── login.html
│   ├── signup.html
│   ├── index.html
└── uploads/
```
