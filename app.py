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

ensure_admin_exists(users_col, config.ADMIN_USERNAME, config.ADMIN_PASSWORD)

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
        username = request.form.get('username').strip()
        password = request.form.get('password')
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        city = request.form.get('city','').strip()
        age = int(request.form['age'])
        blood_group = request.form['blood_group'].strip()

        if users_col.find_one({'username': username}):
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))

        users_col.insert_one({
            'username': username,
            'password_hash': generate_password_hash(password),
            'name': name,
            'email': email,
            'phone': phone,
            'city': city,
            'role': 'user',
            "age": age,
            "blood_group": blood_group,
            'created_at': datetime.now(timezone.utc)
        })
        flash('Signup successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = users_col.find_one({'username': username})
        if not user:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        if check_password_hash(user['password_hash'], password):
            session['user'] = user['username']
            session['role'] = user.get('role', 'user')
            flash('Logged in successfully', 'success')
            # admin goes to admin dashboard
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
    hospitals = list(hospitals_col.find())
    return render_template('admin/dashboard.html', hospitals=hospitals)

@app.route('/admin/hospitals/new', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_new_hospital():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        display_name = request.form.get('display_name').strip()
        password = request.form.get('password')
        email = request.form.get('email','').strip()

        if hospitals_col.find_one({'username': username}):
            flash('Hospital username already exists', 'danger')
            return redirect(url_for('admin_new_hospital'))

        hospitals_col.insert_one({
            'username': username,
            'display_name': display_name,
            'password_hash': generate_password_hash(password),
            'email': email,
            'active': True,
            'created_at': datetime.now(timezone.utc)
        })
        flash('Hospital created', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/new_hospital.html')

@app.route('/hospital/login', methods=['GET', 'POST'])
def hospital_login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
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
            session['hospital_display'] = hospital.get('display_name', hospital['username'])
            flash('Hospital logged in', 'success')
            return redirect(url_for('hospital_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('hospital/login.html')

@app.route('/hospital/dashboard')
@login_required(role='hospital')
def hospital_dashboard():
    hospital_username = session['user']
    donors = list(donors_col.find({'hospital_name': hospital_username}))
    return render_template('hospital/dashboard.html', donors=donors)

@app.route('/hospital/upload', methods=['GET', 'POST'])
@login_required(role='hospital')
def hospital_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{filename}")
            file.save(save_path)

            records = parse_csv_preserve_fields(save_path)
            hospital_name = session['user']
            now = datetime.now(timezone.utc)
            prepared = []
            for rec in records:
                doc = dict(rec)
                doc['hospital_name'] = hospital_name
                doc['uploaded_at'] = now
                prepared.append(doc)
            if prepared:
                donors_col.insert_many(prepared)
                flash(f'Inserted {len(prepared)} donor records.', 'success')
            else:
                flash('No valid records found in CSV.', 'warning')
            return redirect(url_for('hospital_dashboard'))
        else:
            flash('Only CSV files are allowed', 'danger')
            return redirect(request.url)
    return render_template('hospital/upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session or session.get('role') != 'user':
        flash('Please login as a user to search donors.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        organ = request.form.get('organ', '').strip()
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

        candidates = list(donors_col.find(query).limit(2000)) 

        def score_match(doc):
            s = 0
            # 1. Blood Match (Max 150)
            try:
                doc_bg = str(doc.get('Blood_Type', '')).strip()
                if doc_bg and doc_bg.lower() == user_blood.lower():
                    s += 150
                elif doc_bg in valid_donor_groups:
                    s += 100
            except:
                pass
            
            # 2. Age Proximity (Max 60)
            try:
                doc_age = int(doc.get('Age'))
                age_diff = abs(doc_age - user_age)
                s += max(0, 60 - (age_diff * 2))
            except:
                pass

            # 3. Viability / Freshness (Max 50)
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
                        
                        now_utc = datetime.now(timezone.utc)
                        days_elapsed = (now_utc - ua).days
                        viability = max(0, 50 - (days_elapsed * 2))
                        s += viability
            except:
                pass

            return s

        for c in candidates:
            c['_score'] = score_match(c)
            
            # --- ADD DISPLAY DATA FOR VIABILITY ---
            c['days_left_display'] = "Expired"
            try:
                ua = c.get('uploaded_at')
                if ua:
                     # Normalizing to timezone aware if needed
                    if isinstance(ua, str):
                        ua = datetime.fromisoformat(ua)
                    if not ua.tzinfo:
                        ua = ua.replace(tzinfo=timezone.utc)
                    else:
                        ua = ua.astimezone(timezone.utc)
                    
                    now_utc = datetime.now(timezone.utc)
                    days_elapsed = (now_utc - ua).days
                    
                    # Assuming 25 days is the "viable" window based on the scoring logic (50pts / 2pts per day)
                    days_left = 25 - days_elapsed
                    if days_left > 0:
                        c['days_left_display'] = f"{days_left} days"
                    else:
                        c['days_left_display'] = "0 days (Low Viability)"
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

        metrics = {
            'total_matches': total_matches,
            'best_score': best_score,
            'same_blood_count': same_blood_count,
            'avg_age': avg_age if avg_age is not None else 'N/A',
            'age_range': age_range_str,
            'organs_available': ', '.join(sorted(list(organs_available))) if organs_available else 'N/A'
        }

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        timestamp = int(datetime.now(timezone.utc).timestamp())

        charts = []  

        top_n = min(12, len(matches))
        if top_n > 0:
            names = []
            scores = []
            for m in matches[:top_n]:
                lbl = m.get('Name') or m.get('name') or (m.get('hospital_name','') + '_' + str(m.get('_id',''))) 
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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    fullpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(fullpath):
        abort(404)
    return send_file(fullpath, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)