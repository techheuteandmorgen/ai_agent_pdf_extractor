import os
import time
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from sqlalchemy import func
from pikepdf import Pdf
from flask_socketio import SocketIO, emit
from app.models import db, User, Upload
from app.preprocessing import bulk_process_to_excel
from app.preprocessing import process_pdf, bulk_process_to_excel, save_data_to_excel

# Flask App Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Database
db.init_app(app)
migrate = Migrate(app, db)

def print_uploads():
    with app.app_context():
        uploads = Upload.query.all()
        for upload in uploads:
            print(f"User ID: {upload.user_id}, Total Premium: {upload.total_premium}, "
                  f"Commission: {upload.commission}, Net Premium: {upload.net_premium}")


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

dashboard_data = {
    "total_premium_all_time": 0,
    "total_commission_all_time": 0,
}


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
        output_file = None
        session_id = str(uuid.uuid4())  # Unique identifier for the session
        output_file_name = f'consolidated_data_{session_id}.xlsx'
        total_files = len(files)
        processed_files = 0

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_folder, filename)
                file.save(file_path)

                if is_valid_pdf(file_path):
                    valid_files.append(file_path)
                    processed_files += 1

                    # Emit progress update
                    socketio.emit(
                        "upload_status",
                        {
                            "file_name": filename,
                            "status": "Uploaded",
                            "processed_files": processed_files,
                            "total_files": total_files,
                        },
                        namespace="/"
                    )
                else:
                    os.remove(file_path)

        if valid_files:
            # Consolidate extracted data into an Excel file
            output_file = os.path.join(app.config['OUTPUT_FOLDER'], output_file_name)
            bulk_process_to_excel(temp_folder, output_file, current_user.id)  # Updated function

            # Clean up the temporary folder
            for file in os.listdir(temp_folder):
                os.remove(os.path.join(temp_folder, file))
            os.rmdir(temp_folder)

        # Emit the download link or failure message
        if output_file and os.path.exists(output_file):
            socketio.emit(
                "upload_status",
                {
                    "file_name": output_file_name,
                    "status": "Processed Successfully",
                    "link": url_for('download_file', filename=output_file_name),
                },
                namespace="/"
            )
        else:
            socketio.emit(
                "upload_status",
                {"file_name": "N/A", "status": "Processing Failed"},
                namespace="/"
            )

    return render_template('upload.html')

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash("File not found!", "danger")
    return redirect(url_for('upload'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('upload'))

    # Total Premium and Commission Calculations
    total_premium_all_time = db.session.query(func.sum(Upload.total_premium)).scalar() or 0
    total_commission_all_time = db.session.query(func.sum(Upload.commission)).scalar() or 0

    # User-wise Summary With Outer Join
    user_summary = db.session.query(
        User.username,
        func.count(Upload.id).label('uploads'),
        func.sum(Upload.total_premium).label('total_premium'),
        func.sum(Upload.commission).label('total_commission')
    ).outerjoin(Upload).group_by(User.id).all()

    # Debugging Outputs
    print(f"DEBUG: Total Premium (All Time): {total_premium_all_time}")
    print(f"DEBUG: Total Commission (All Time): {total_commission_all_time}")
    print(f"DEBUG: User Summary: {user_summary}")

    # Ensure correct data is passed to the template
    return render_template(
        'dashboard.html',
        total_premium_all_time=total_premium_all_time,
        total_commission_all_time=total_commission_all_time,
        user_summary=user_summary
    )

@app.route('/api/dashboard_data', methods=['GET'])
@login_required
def get_dashboard_data():
    # Calculate total premium and total commission all time
    total_premium_all_time = db.session.query(func.sum(Upload.total_premium)).scalar() or 0
    total_commission_all_time = db.session.query(func.sum(Upload.commission)).scalar() or 0

    # Calculate daily premium and daily commission (for current day)
    daily_premium = db.session.query(func.sum(Upload.total_premium)).filter(
        func.date(Upload.upload_date) == func.date(datetime.utcnow())
    ).scalar() or 0
    daily_commission = daily_premium * 0.05  # Example: assuming 5% commission rate

    # Fetch user-wise data (summary for table and chart)
    user_summary = db.session.query(
        User.username,
        func.count(Upload.id).label('uploads'),
        func.sum(Upload.total_premium).label('total_premium'),
        func.sum(Upload.commission).label('total_commission'),
        func.sum(Upload.total_premium - Upload.commission).label('net_premium')
    ).join(Upload).group_by(User.id).all()

    # Prepare user data for frontend
    user_data = [
        {
            "username": user.username or "Unknown User",  # Fallback if username is None
            "uploads": user.uploads or 0,
            "total_premium": user.total_premium or 0,
            "total_commission": user.total_commission or 0,
            "net_premium": user.net_premium or 0,
        }
        for user in user_summary
    ]

    # Return data as JSON for frontend consumption
    return jsonify({
        "total_premium_all_time": total_premium_all_time,
        "total_commission_all_time": total_commission_all_time,
        "daily_premium": daily_premium,
        "daily_commission": daily_commission,
        "user_summary": user_data
    })

# API Routes
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
def user_uploads_data():
    user_summary = db.session.query(
        User.username,
        func.count(Upload.id).label('uploads'),
        func.sum(Upload.total_premium).label('total_premium'),
        func.sum(Upload.commission).label('commission'),
        func.sum(Upload.total_premium - Upload.commission).label('net_premium')
    ).join(Upload).group_by(User.username).all()

    response_data = [
        {
            "username": row.username or "Unknown User",
            "uploads": row.uploads or 0,
            "total_premium": row.total_premium or 0,
            "commission": row.commission or 0,
            "net_premium": row.net_premium or 0
        }
        for row in user_summary
    ]

    return jsonify(response_data)
    


if __name__ == '__main__':
    socketio.run(app, debug=True)