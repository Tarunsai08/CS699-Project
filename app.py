import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import config
from helpers import parse_csv_preserve_fields, ensure_admin_exists
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from bson import ObjectId

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = MongoClient(config.MONGODB_URI, tls=True)
db = client[config.DB_NAME]
users_col = db['users']       
hospitals_col = db['hospitals']
donors_col = db['donors']
organ_requests_col = db['organ_requests']

ensure_admin_exists(users_col, config.ADMIN_USERNAME, config.ADMIN_PASSWORD)

def now_utc():
    return datetime.now(timezone.utc)

def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user' not in session:
                flash('Please login first', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        age = request.form.get('age', '').strip()
        blood_group = request.form.get('blood_group', '').strip()

        # Validation checks
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long', 'danger')
            return redirect(url_for('signup'))
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return redirect(url_for('signup'))
        
        if not name:
            flash('Name is required', 'danger')
            return redirect(url_for('signup'))
        
        if not email or '@' not in email:
            flash('Valid email is required', 'danger')
            return redirect(url_for('signup'))
        
        if not phone or not phone.isdigit() or len(phone) < 10:
            flash('Valid phone number (at least 10 digits) is required', 'danger')
            return redirect(url_for('signup'))
        
        if not city:
            flash('City is required', 'danger')
            return redirect(url_for('signup'))
        
        try:
            age_int = int(age)
            if age_int < 18 or age_int > 120:
                flash('Age must be between 18 and 120', 'danger')
                return redirect(url_for('signup'))
        except (ValueError, TypeError):
            flash('Valid age is required', 'danger')
            return redirect(url_for('signup'))
        
        valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if not blood_group or blood_group not in valid_blood_groups:
            flash('Valid blood group is required', 'danger')
            return redirect(url_for('signup'))

        if users_col.find_one({'username': username}):
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))
        
        if users_col.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))

        users_col.insert_one({
            'username': username,
            'password_hash': generate_password_hash(password),
            'name': name,
            'email': email,
            'phone': phone,
            'city': city,
            'role': 'user',
            'age': age_int,
            'blood_group': blood_group,
            'created_at': now_utc()
        })
        flash('Signup successful. Please login.', 'success')
        return redirect(url_for('login'))
       
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation checks
        if not username:
            flash('Username is required', 'danger')
            return redirect(url_for('login'))
        
        if not password:
            flash('Password is required', 'danger')
            return redirect(url_for('login'))
        
        user = users_col.find_one({'username': username})
        if not user:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        if check_password_hash(user['password_hash'], password):
            session['user'] = user['username']
            session['role'] = user.get('role', 'user')
            flash('Logged in successfully', 'success')
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    query = request.args.get('q', '').strip()

    if query:
        hospitals = list(hospitals_col.find({
            '$or': [
                {'username': {'$regex': query, '$options': 'i'}},
                {'display_name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}}
            ]
        }))
    else:
        hospitals = list(hospitals_col.find())

    return render_template('admin/dashboard.html', hospitals=hospitals, query=query)

@app.route('/admin/hospitals/new', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_new_hospital():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()

        # Validation checks
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long', 'danger')
            return redirect(url_for('admin_new_hospital'))
        
        if not display_name:
            flash('Display name is required', 'danger')
            return redirect(url_for('admin_new_hospital'))
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return redirect(url_for('admin_new_hospital'))
        
        if email and '@' not in email:
            flash('Valid email is required', 'danger')
            return redirect(url_for('admin_new_hospital'))

        if hospitals_col.find_one({'username': username}):
            flash('Hospital username already exists', 'danger')
            return redirect(url_for('admin_new_hospital'))

        hospitals_col.insert_one({
            'username': username,
            'display_name': display_name,
            'password_hash': generate_password_hash(password),
            'email': email,
            'active': True,
            'created_at': now_utc()
        })
        flash('Hospital created', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/new_hospital.html')

@app.route('/admin/hospital/<hos_id>/edit', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_edit_hospital(hos_id):
    hospital = hospitals_col.find_one({'_id': ObjectId(hos_id)})
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        existing = hospitals_col.find_one({'username': username, '_id': {'$ne': hospital['_id']}})
        if existing:
            flash('Username already in use.', 'danger')
            return redirect(request.url)

        if not display_name or not username:
            flash('Username and Institution Name are required', 'danger')
            return redirect(request.url)
        


        update_data = {
            'display_name': display_name,
            'email': email,
            'username': username
        }

        if password:  
            update_data['password_hash'] = generate_password_hash(password)

        hospitals_col.update_one(
            {'_id': ObjectId(hos_id)},
            {'$set': update_data}
        )

        flash('Hospital updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_hospital.html', hospital=hospital)

@app.route('/admin/hospital/<hos_id>/delete')
@login_required(role='admin')
def admin_delete_hospital(hos_id):
    hospital = hospitals_col.find_one({'_id': ObjectId(hos_id)})
    if not hospital:
        flash('Hospital not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    donors_col.delete_many({'hospital_id': hospital['_id']})

    hospitals_col.delete_one({'_id': ObjectId(hos_id)})

    flash('Hospital and all related donor records deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/requests/<req_id>/action', methods=['POST'])
@login_required(role='admin')
def admin_handle_request_action(req_id):
    action = request.form.get('action')   
    req = organ_requests_col.find_one({'_id': ObjectId(req_id)})

    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for('admin_requests'))

    if action == "reject":
        organ_requests_col.update_one(
            {'_id': req['_id']},
            {'$set': {'status': 'rejected', 'updated_at': now_utc()}}
        )
        flash("Request rejected.", "info")
        return redirect(url_for('admin_requests'))

    if action == "approve":
        organ_requests_col.update_one(
            {'_id': req['_id']},
            {'$set': {'status': 'approved', 'updated_at': now_utc()}}
        )

        best_donor, best_score = allocate_for_request(req)

        if best_donor:
            flash("Organ successfully allocated.", "success")
        else:
            flash("No suitable donor found. Request marked as failed.", "warning")

        return redirect(url_for('admin_requests'))

    flash("Invalid action.", "danger")
    return redirect(url_for('admin_requests'))

@app.route('/admin/requests')
@login_required(role='admin')
def admin_requests():
    reqs = list(organ_requests_col.find().sort('created_at', -1))

    user_ids = list({r['user_id'] for r in reqs})
    user_map = {
        u['_id']: u
        for u in users_col.find({'_id': {'$in': user_ids}})
    }

    for r in reqs:
        r['user'] = user_map.get(r['user_id'])

    return render_template('admin/requests.html', reqs=reqs)

@app.route('/hospital/login', methods=['GET', 'POST'])
def hospital_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation checks
        if not username:
            flash('Username is required', 'danger')
            return redirect(url_for('hospital_login'))
        
        if not password:
            flash('Password is required', 'danger')
            return redirect(url_for('hospital_login'))
        
        hospital = hospitals_col.find_one({'username': username})
        if not hospital:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('hospital_login'))
        if not hospital.get('active', True):
            flash('Hospital account not active', 'danger')
            return redirect(url_for('hospital_login'))
        if check_password_hash(hospital['password_hash'], password):
            session['user'] = hospital['username']
            session['role'] = 'hospital'
            session['hospital_id'] = str(hospital['_id'])
            session['hospital_display'] = hospital.get('display_name', hospital['username'])
            flash('Hospital logged in', 'success')
            return redirect(url_for('hospital_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('hospital/login.html')

@app.route('/hospital/dashboard')
@login_required(role='hospital')
def hospital_dashboard():
    q = request.args.get('q', '').strip()

    base_filter = {'hospital_id': ObjectId(session['hospital_id']),'is_allocated': {'$ne': True}}

    if q:
        donors = list(donors_col.find({
            '$and': [
                base_filter,
                {'$or': [
                    {'Name': {'$regex': q, '$options': 'i'}},
                    {'Organ': {'$regex': q, '$options': 'i'}},
                    {'Blood_Type': {'$regex': q, '$options': 'i'}},
                ]}
            ]
        }))
    else:
        donors = list(donors_col.find(base_filter))

    return render_template('hospital/dashboard.html', donors=donors, query=q)

@app.route('/hospital/upload', methods=['GET', 'POST'])
@login_required(role='hospital')
def hospital_upload():
    if request.method == 'POST':
        # Validation checks
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if not file or file.filename == '' or file.filename is None:
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Only CSV files are allowed', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{now_utc().strftime('%Y%m%d%H%M%S')}_{filename}")
            file.save(save_path)

            records = parse_csv_preserve_fields(save_path)
            hospital_name = session['user']
            now = now_utc()
            prepared = []
            for rec in records:
                doc = dict(rec)
                doc['hospital_id'] = ObjectId(session['hospital_id'])
                doc['uploaded_at'] = now
                doc['is_allocated'] = False
                doc['allocated_to_request_id'] = None
                doc['allocated_at'] = None
                prepared.append(doc)
            if prepared:
                donors_col.insert_many(prepared)
                flash(f'Inserted {len(prepared)} donor records.', 'success')
            else:
                flash('No valid records found in CSV.', 'warning')
            return redirect(url_for('hospital_dashboard'))
    return render_template('hospital/upload.html')

@app.route('/hospital/donor/<donor_id>/edit', methods=['GET', 'POST'])
@login_required(role='hospital')
def hospital_edit_donor(donor_id):

    donor = donors_col.find_one({'_id': ObjectId(donor_id)})
    if not donor:
        flash('Donor not found.', 'danger')
        return redirect(url_for('hospital_dashboard'))

    # Ensure this donor belongs to this hospital
    if str(donor.get('hospital_id')) != session['hospital_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('hospital_dashboard'))

    if request.method == 'POST':
        updates = {}
        protected_fields = ['_id', 'hospital_id', 'uploaded_at',
                            'is_allocated', 'allocated_to_request_id', 'allocated_at']
        for key in donor.keys():
            if key not in protected_fields:
                value = request.form.get(key)
                if value is not None:
                    updates[key] = value

        donors_col.update_one(
            {'_id': ObjectId(donor_id)},
            {'$set': updates}
        )

        flash('Donor updated successfully.', 'success')
        return redirect(url_for('hospital_dashboard'))

    return render_template('hospital/edit_donor.html', donor=donor)

def score_match(doc, user_age, user_blood, valid_donor_groups):
    s = 0
    try:
        doc_bg = str(doc.get('Blood_Type', '')).strip()
        if doc_bg and doc_bg.lower() == user_blood.lower():
            s += 150
        elif doc_bg in valid_donor_groups:
            s += 100
        else:
            return -1
    except:
        pass
    
    try:
        doc_age = int(doc.get('Age'))
        age_diff = abs(doc_age - user_age)
        s += max(0, 60 - (age_diff * 2))
    except:
        pass

    try:
        ua = doc.get('uploaded_at')
        if ua:
            if isinstance(ua, str):
                try:
                    ua = datetime.fromisoformat(ua)
                except:
                    ua = None
            if ua:
                if not ua.tzinfo:
                    ua = ua.replace(tzinfo=timezone.utc)
                else:
                    ua = ua.astimezone(timezone.utc)
                
                now_time = now_utc()
                days_elapsed = (now_time - ua).days
                viability = max(0, 50 - (days_elapsed * 2))
                s += viability
    except:
        pass

    return s


@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session or session.get('role') != 'user':
        flash('Please login as a user to search donors.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        organ = request.form.get('organ', '').strip()
        
        # Validation checks
        if not organ:
            flash('Please select an organ to search for', 'danger')
            return redirect(url_for('search'))
        
        user = users_col.find_one({'username': session['user']})
        if not user:
            flash('User data not found. Please login again.', 'danger')
            return redirect(url_for('login'))

        try:
            user_age = int(user.get('age'))
        except Exception:
            flash('Your profile missing a valid age. Edit profile to add age.', 'danger')
            return redirect(url_for('index'))
        user_blood = user.get('blood_group', '').strip()
        if not user_blood:
            flash('Your profile missing blood group. Edit profile to add blood group.', 'danger')
            return redirect(url_for('index'))

        BLOOD_COMPATIBILITY = {
            "O-": ["O-"],
            "O+": ["O-", "O+"],
            "A-": ["A-", "O-"],
            "A+": ["A+", "A-", "O+", "O-"],
            "B-": ["B-", "O-"],
            "B+": ["B+", "B-", "O+", "O-"],
            "AB-": ["AB-", "A-", "B-", "O-"],
            "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
        }
        valid_donor_groups = BLOOD_COMPATIBILITY.get(user_blood, [])

        ORGAN_AGE_TOLERANCES = {
            "Kidney": 15,
            "Liver": 20,
            "Heart": 10,
            "Lung": 10,
            "Cornea": 40,
            "Pancreas": 15,
            "Default": 10
        }
        tol = ORGAN_AGE_TOLERANCES.get(organ.title(), ORGAN_AGE_TOLERANCES['Default'])
        age_min = max(0, user_age - tol)
        age_max = user_age + tol

        query = {}
        if organ:
            query['Organ'] = {'$regex': f'^{organ}$', '$options': 'i'}
        if valid_donor_groups:
            query['Blood_Type'] = {'$in': valid_donor_groups}
        query['Age'] = {'$gte': age_min, '$lte': age_max}
        query['is_allocated'] = {'$ne': True}

        candidates = list(donors_col.find(query).limit(2000)) 

        for c in candidates:
            c['_score'] = score_match(c, user_age, user_blood, valid_donor_groups)
            
            c['days_left_display'] = "Expired"
            try:
                ua = c.get('uploaded_at')
                if ua:
                    if isinstance(ua, str):
                        ua = datetime.fromisoformat(ua)
                    if not ua.tzinfo:
                        ua = ua.replace(tzinfo=timezone.utc)
                    else:
                        ua = ua.astimezone(timezone.utc)
                    
                    current_time = now_utc()
                    days_elapsed = (current_time - ua).days
                    
                    days_left = 25 - days_elapsed
                    if days_left > 0:
                        c['days_left_display'] = f"{days_left} Hours"
                    else:
                        c['days_left_display'] = "0 Hours (Low Viability)"
            except:
                c['days_left_display'] = "Unknown"


        matches = sorted(candidates, key=lambda x: x.get('_score', 0), reverse=True)

        total_matches = len(matches)
        best_score = round(matches[0]['_score'], 1) if total_matches else 0
        same_blood_count = sum(1 for m in matches if str(m.get('Blood_Type','')).strip().lower() == user_blood.lower())
        avg_age = None
        ages = []
        organs_available = set()
        for m in matches:
            if 'Age' in m:
                try:
                    ages.append(int(m['Age']))
                except:
                    pass
            organs_available.add(m.get('Organ','Unknown'))
        if ages:
            avg_age = round(sum(ages)/len(ages), 1)
        age_range_str = f"{age_min} - {age_max}"

        hospital_ids = list({m['hospital_id'] for m in matches if 'hospital_id' in m})
        hospital_map = {
            str(h['_id']): h
            for h in hospitals_col.find({'_id': {'$in': hospital_ids}})
        }

        for m in matches:
            hid = str(m.get('hospital_id'))
            hospital = hospital_map.get(hid)
            m['hospital_display'] = hospital['display_name'] if hospital else 'Unknown'

        metrics = {
            'total_matches': total_matches,
            'best_score': best_score,
            'same_blood_count': same_blood_count,
            'avg_age': avg_age if avg_age is not None else 'N/A',
            'age_range': age_range_str,
            'organs_available': ', '.join(sorted(list(organs_available))) if organs_available else 'N/A'
        }

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        timestamp = int(now_utc().timestamp())

        charts = []  

        top_n = min(12, len(matches))
        if top_n > 0:
            names = []
            scores = []
            for m in matches[:top_n]:
                lbl = (
                    m.get('Name')
                    or m.get('name')
                    or (m.get('hospital_display', '') + '_' + str(m.get('_id', '')))
                )
                names.append(lbl if len(lbl)<=20 else lbl[:18] + '..')
                scores.append(m.get('_score', 0))

            plt.figure(figsize=(8,4))
            sns.barplot(x=scores, y=names)
            plt.xlabel('Match score')
            plt.ylabel('Donor')
            plt.title('Top donor matches (score)')
            plt.tight_layout()
            fname = f"bar_{timestamp}.png"
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            plt.savefig(fpath, bbox_inches='tight')
            plt.close()
            charts.append({'label':'Top donor scores','filename':fname})

        if ages:
            diffs = []
            idxs = []
            for i, m in enumerate(matches[:50]): 
                try:
                    md = int(m.get('Age'))
                    diffs.append(abs(md - user_age))
                except:
                    diffs.append(None)
                idxs.append(i+1)
            plt.figure(figsize=(8,3))
            plt.plot(idxs, [d if d is not None else 0 for d in diffs], marker='o')
            plt.xlabel('Match rank')
            plt.ylabel('Age difference (years)')
            plt.title('Age difference of top matches')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            fname = f"line_{timestamp}.png"
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            plt.savefig(fpath, bbox_inches='tight')
            plt.close()
            charts.append({'label':'Age difference trend','filename':fname})

        upload_days = {}
        for m in matches:
            ua = m.get('uploaded_at')
            if ua:
                try:
                    day = ua.astimezone(timezone.utc).date() if hasattr(ua, 'astimezone') else ua.date()
                except:
                    try:
                        day = datetime.fromisoformat(str(ua)).date()
                    except:
                        continue
                upload_days[str(day)] = upload_days.get(str(day), 0) + 1
        if upload_days:
            items = sorted(upload_days.items())
            days = [it[0] for it in items]
            counts = [it[1] for it in items]
            plt.figure(figsize=(8,3))
            plt.plot(days, counts, marker='o')
            plt.xticks(rotation=30)
            plt.xlabel('Upload day')
            plt.ylabel('Matches added')
            plt.title('Matches by upload day')
            plt.tight_layout()
            fname = f"timeline_{timestamp}.png"
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            plt.savefig(fpath, bbox_inches='tight')
            plt.close()
            charts.append({'label':'Matches timeline','filename':fname})

        bcounts = {}
        for m in matches:
            bg = m.get('Blood_Type') or m.get('Blood_type') or 'Unknown'
            bg = str(bg).strip()
            bcounts[bg] = bcounts.get(bg, 0) + 1
        if bcounts:
            labels = list(bcounts.keys())
            sizes = list(bcounts.values())
            plt.figure(figsize=(6,4))
            plt.pie(sizes, labels=labels, autopct='%1.0f%%', textprops={'fontsize':8})
            plt.title('Blood groups among matches')
            plt.tight_layout()
            fname = f"pie_{timestamp}.png"
            fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            plt.savefig(fpath, bbox_inches='tight')
            plt.close()
            charts.append({'label':'Blood group distribution','filename':fname})

        for m in matches:
            if '_id' in m:
                m['_id'] = str(m['_id'])
            if 'uploaded_at' in m:
                try:
                    m['uploaded_at_display'] = m['uploaded_at'].astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')
                except:
                    try:
                        m['uploaded_at_display'] = str(m['uploaded_at'])
                    except:
                        m['uploaded_at_display'] = '-'

        return render_template('results.html', matches=matches, charts=charts, metrics=metrics, user_age=user_age, user_blood=user_blood)

    return render_template('search.html')

def allocate_for_request(request_doc):
    """
    request_doc: a document from organ_requests_col
    Returns: (best_donor, best_score) or (None, None)
    """

    organ = request_doc.get('organ')
    user_id = request_doc.get('user_id')
    user = users_col.find_one({'_id': user_id})
    if not user:
        return None, None

    try:
        user_age = int(user.get('age'))
    except:
        return None, None

    user_blood = user.get('blood_group', '').strip()
    if not user_blood:
        return None, None

    BLOOD_COMPATIBILITY = {
        "O-": ["O-"],
        "O+": ["O-", "O+"],
        "A-": ["A-", "O-"],
        "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"],
        "B+": ["B+", "B-", "O+", "O-"],
        "AB-": ["AB-", "A-", "B-", "O-"],
        "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
    }
    valid_donor_groups = BLOOD_COMPATIBILITY.get(user_blood, [])

    ORGAN_AGE_TOLERANCES = {
        "Kidney": 15,
        "Liver": 20,
        "Heart": 10,
        "Lung": 10,
        "Cornea": 40,
        "Pancreas": 15,
        "Default": 10
    }
    tol = ORGAN_AGE_TOLERANCES.get(organ.title(), ORGAN_AGE_TOLERANCES['Default'])
    age_min = max(0, user_age - tol)
    age_max = user_age + tol

    # Only available donors, not yet allocated
    query = {
        'Organ': {'$regex': f'^{organ}$', '$options': 'i'},
        'Blood_Type': {'$in': valid_donor_groups},
        'Age': {'$gte': age_min, '$lte': age_max},
        'is_allocated': {'$ne': True}
    }

    candidates = list(donors_col.find(query).limit(2000))

    best_donor = None
    best_score = -1

    for d in candidates:
        s = score_match(d, user_age, user_blood, valid_donor_groups)
        if s > best_score:
            best_score = s
            best_donor = d

    if not best_donor or best_score < 0:
        # Mark request as failed
        organ_requests_col.update_one(
            {'_id': request_doc['_id']},
            {'$set': {
                'status': 'failed',
                'updated_at': now_utc()
            }}
        )
        return None, None

    # MARK DONOR AS ALLOCATED
    donors_col.update_one(
        {'_id': best_donor['_id']},
        {'$set': {
            'is_allocated': True,
            'allocated_to_request_id': request_doc['_id'],
            'allocated_at': now_utc()
        }}
    )

    # MARK REQUEST AS MATCHED
    organ_requests_col.update_one(
        {'_id': request_doc['_id']},
        {'$set': {
            'status': 'matched',
            'matched_donor_id': best_donor['_id'],
            'match_score': best_score,
            'updated_at': now_utc()
        }}
    )

    return best_donor, best_score

@app.route('/request-organ', methods=['GET', 'POST'])
@login_required(role='user')
def request_organ():
    if request.method == 'POST':
        organ = request.form.get('organ', '').strip()

        if not organ:
            flash('Please select an organ.', 'danger')
            return redirect(request.url)

        req = {
            'user_id': users_col.find_one({'username': session['user']})['_id'],
            'organ': organ,
            'status': 'pending',
            'created_at': now_utc(),
            'updated_at': now_utc()
        }

        organ_requests_col.insert_one(req)
        flash('Organ request submitted. Await admin approval.', 'success')
        return redirect(url_for('my_requests'))

    return render_template('request_organ.html')

@app.route('/my-requests')
@login_required(role='user')
def my_requests():
    user = users_col.find_one({'username': session['user']})
    reqs = list(organ_requests_col.find({'user_id': user['_id']}))
    donor_ids = [
        req['matched_donor_id']
        for req in reqs
        if req.get('matched_donor_id')
    ]

    donor_ids = [ObjectId(d) for d in donor_ids]
    donor_map = {
        str(d['_id']): d
        for d in donors_col.find({'_id': {'$in': donor_ids}})
    }

    hospital_ids = list({
        d['hospital_id']
        for d in donor_map.values()
        if d.get('hospital_id')
    })

    hospital_map = {
        str(h['_id']): h
        for h in hospitals_col.find({'_id': {'$in': hospital_ids}})
    }

    for req in reqs:
        donor_id = req.get('matched_donor_id')
        if donor_id:
            donor = donor_map.get(str(donor_id))
            if donor:
                req['donor_name'] = donor.get('Name', 'Unknown Donor')
                req['donor_blood'] = donor.get('Blood_Type', '-')
                req['donor_age'] = donor.get('Age', '-')

                hospital = hospital_map.get(str(donor.get('hospital_id')))
                req['hospital_name'] = hospital.get('display_name') if hospital else "Unknown Hospital"
            else:
                req['donor_name'] = "Unknown Donor"
                req['hospital_name'] = "Unknown Hospital"

    return render_template('my_requests.html', reqs=reqs)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    fullpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(fullpath):
        abort(404)
    return send_file(fullpath, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)