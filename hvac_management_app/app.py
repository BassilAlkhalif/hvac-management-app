import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hvac_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "123456"

# Path for uploads folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file size limit

db = SQLAlchemy(app)

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Model
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    technician_name = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    job_status = db.Column(db.String(50), default='scheduled')
    scheduled_date = db.Column(db.String(50))
    before_photo = db.Column(db.String(200))
    after_photo = db.Column(db.String(200))
    completion_time = db.Column(db.String(50))
    notes = db.Column(db.String(500))

# Initialize the database
if not os.path.exists('hvac_management.db'):
    with app.app_context():
        db.create_all()

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Home Route
@app.route('/')
def home():
    jobs = Job.query.filter(Job.job_status != 'completed').all()
    return render_template('index.html', jobs=jobs)

# Perform Job Route
@app.route('/perform_job/<int:job_id>', methods=['GET', 'POST'])
def perform_job(job_id):
    job = Job.query.get(job_id)

    if not job:
        flash("Job not found!", "danger")
        return redirect(url_for('home'))

    try:
        if request.method == 'POST':
            before_photo = request.files.get('before_photo')
            after_photo = request.files.get('after_photo')
            comment = request.form.get('comment')

            if before_photo:
                before_filename = f"{job_id}_before_{int(time.time())}_{secure_filename(before_photo.filename)}"
                before_filepath = os.path.join(app.config['UPLOAD_FOLDER'], before_filename)
                before_photo.save(before_filepath)
                job.before_photo = before_filename
                logging.debug(f"Before photo saved at: {before_filepath}")

            if after_photo:
                after_filename = f"{job_id}_after_{int(time.time())}_{secure_filename(after_photo.filename)}"
                after_filepath = os.path.join(app.config['UPLOAD_FOLDER'], after_filename)
                after_photo.save(after_filepath)
                job.after_photo = after_filename
                logging.debug(f"After photo saved at: {after_filepath}")

            job.notes = comment
            job.job_status = 'completed'
            job.completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.commit()
            flash("Job completed successfully!", "success")
            return redirect(url_for('home'))

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('home'))

    return render_template('perform_job.html', job=job)

# Job Details Route
@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    job = Job.query.get(job_id)
    if not job:
        flash("Job not found!", "danger")
        return redirect(url_for('view_jobs'))

    before_photo_url = url_for('uploaded_file', filename=job.before_photo) if job.before_photo else None
    after_photo_url = url_for('uploaded_file', filename=job.after_photo) if job.after_photo else None

    return render_template('job_details.html', job=job, before_photo_url=before_photo_url, after_photo_url=after_photo_url)

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    try:
        total_jobs = Job.query.count()
        completed_jobs = Job.query.filter_by(job_status='completed').count()
        pending_jobs = total_jobs - completed_jobs

        technician_data = db.session.query(Job.technician_name, db.func.count(Job.id)).group_by(Job.technician_name).all()
        technician_names = [data[0] for data in technician_data]
        technician_counts = [data[1] for data in technician_data]

        stats = {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "pending_jobs": pending_jobs,
            "technician_names": technician_names,
            "technician_counts": technician_counts
        }

        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logging.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('home'))

# Run the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
