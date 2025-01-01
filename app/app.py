import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from app.preprocessing import bulk_process_to_excel
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploaded_pdfs'
app.config['OUTPUT_FOLDER'] = 'output_data'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

VALID_USERNAME = 'admin'
VALID_PASSWORD = 'password123'

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Ensure authentication for protected routes
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/', methods=['GET'])
def home():
    # Redirect to login page if not logged in
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    # Redirect to upload page if already logged in
    return redirect(url_for('upload'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to upload page
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('upload'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('upload'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('logged_in', None)  # Clear session
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))  # Redirect to login page after logout

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # File upload logic
    if request.method == 'POST':
        # Clear old files
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))

        if 'files' not in request.files or request.files['files'].filename == '':
            flash('No files selected. Please try again.', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Process files
        input_folder = app.config['UPLOAD_FOLDER']
        output_excel_path = os.path.join(app.config['OUTPUT_FOLDER'], 'consolidated_data.xlsx')
        bulk_process_to_excel(input_folder, output_excel_path)

        flash('Files uploaded successfully. Processing complete!', 'success')
        return redirect(url_for('download'))

    return render_template('upload.html')

@app.route('/download', methods=['GET'])
@login_required
def download():
    output_excel_path = os.path.join(app.config['OUTPUT_FOLDER'], 'consolidated_data.xlsx')
    if os.path.exists(output_excel_path):
        return render_template('download.html', download_ready=True)

    flash('No processed file found. Please upload files first.', 'danger')
    return render_template('download.html', download_ready=False)

@app.route('/download_excel', methods=['GET'])
@login_required
def download_excel():
    try:
        output_excel_path = os.path.abspath(os.path.join(app.root_path, '..', 'output_data', 'consolidated_data.xlsx'))
        if os.path.exists(output_excel_path):
            return send_file(output_excel_path, as_attachment=True)
        else:
            flash('No processed file found. Please upload and process files first.', 'danger')
    except Exception as e:
        flash(f'Error while preparing download: {e}', 'danger')
    return redirect(url_for('upload'))

if __name__ == '__main__':
    app.run(debug=True)