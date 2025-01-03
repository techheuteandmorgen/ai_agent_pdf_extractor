import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from sqlalchemy import func
from pikepdf import Pdf
from app.models import db, User, Upload
from app.preprocessing import bulk_process_to_excel
import uuid
import logging

# Flask App Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# Initialize Database
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User Loader
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploaded_pdfs'
app.config['OUTPUT_FOLDER'] = os.path.abspath('output_data')
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_valid_pdf(file_path):
    try:
        with Pdf.open(file_path):
            return True
    except Exception as e:
        logger.error(f"Invalid PDF: {e}")
        return False

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('upload'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"Welcome, {user.username}!", 'success')

            if user.role == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('upload'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    temp_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
    os.makedirs(temp_folder, exist_ok=True)

    if request.method == 'POST':
        if 'files' not in request.files or not request.files.getlist('files'):
            flash('No files selected. Please try again.', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files')
        valid_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_folder, filename)
                file.save(file_path)

                if is_valid_pdf(file_path):
                    valid_files.append(file_path)
                else:
                    os.remove(file_path)

        if not valid_files:
            flash('No valid files uploaded. Please try again.', 'danger')
            return redirect(request.url)

        session_id = str(uuid.uuid4())
        output_file = os.path.join(app.config['OUTPUT_FOLDER'], f'consolidated_data_{session_id}.xlsx')
        bulk_process_to_excel(temp_folder, output_file)

        for file in os.listdir(temp_folder):
            os.remove(os.path.join(temp_folder, file))
        os.rmdir(temp_folder)

        flash('Files uploaded and processed successfully!', 'success')
        return redirect(url_for('download_page', filename=f'consolidated_data_{session_id}.xlsx'))

    return render_template('upload.html')

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download the specified file."""
    # Correctly construct the file path
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    # Check if the file exists in the correct folder
    if not os.path.exists(file_path):
        flash(f"File '{filename}' not found. Please try uploading files again.", 'danger')
        return redirect(url_for('upload'))
    
    # Serve the file for download
    return send_file(file_path, as_attachment=True)

@app.route('/download')
@login_required
def download_page():
    filename = request.args.get('filename')
    if not filename:
        flash("No file available for download.", "danger")
        return redirect(url_for('upload'))
    return render_template('download.html', filename=filename)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('upload'))
    return render_template('dashboard.html', users=User.query.all())


@app.route('/api/all_time_premium', methods=['GET'])
@login_required
def api_all_time_premium():
    try:
        all_time_premium = db.session.query(func.sum(Upload.total_premium)).scalar() or 0
        return jsonify({'all_time_premium': float(all_time_premium)})
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching data.', 'details': str(e)}), 500

@app.route('/api/daily_premium', methods=['GET'])
@login_required
def api_daily_premium():
    try:
        daily_premium = db.session.query(
            func.sum(Upload.total_premium)
        ).filter(
            func.date(Upload.upload_date) == func.date(func.now())
        ).scalar() or 0
        return jsonify({'daily_premium': float(daily_premium)})
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching data.', 'details': str(e)}), 500

@app.route('/api/user_uploads', methods=['GET'])
@login_required
def api_user_uploads():
    try:
        uploads = db.session.query(
            Upload.user_id,
            func.count(Upload.id).label('uploads'),
            func.sum(Upload.total_premium).label('total_premium')
        ).group_by(Upload.user_id).all()

        result = [
            {
                'user': User.query.get(u[0]).username,
                'uploads': u[1],
                'total_premium': float(u[2]) if u[2] else 0.0
            } for u in uploads
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching data.', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)