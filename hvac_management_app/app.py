import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import time
import cloudinary
import cloudinary.uploader

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hvac_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "123456"

# Configure Cloudinary
cloudinary.config(
    cloud_name="dc3tb4drj",
    api_key="189685417282461",
    api_secret="vOCqr2HynRmm04m9DKT-8mFkDLg"
)

db = SQLAlchemy(app)

# Ensure the uploads folder exists (for local testing only)
UPLOAD_FOLDER = 'uploads'
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
    before_photo_url = db.Column(db.String(500))
    after_photo_url = db.Column(db.String(500))
    completion_time = db.Column(db.String(50))
    notes = db.Column(db.String(500))

# Initialize the database
if not os.path.exists('hvac_management.db'):
    with app.app_context():
        db.create_all()

# Upload file to Cloudinary and return the URL
def upload_to_cloudinary(file):
    try:
        result = cloudinary.uploader.upload(file)
        return result['secure_url']
    except Exception as e:
        logging.error(f"Error uploading file to Cloudinary: {str(e)}")
        return None

# Home Route
@app.route('/')
def home():
    jobs = Job.query.filter(Job.job_status != 'completed').all()
    return render_template('index.html', jobs=jobs)

# Create New Job Route
@app.route('/create_job', methods=['GET', 'POST'])
def create_job():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        technician_name = request.form.get('technician_name')
        job_type = request.form.get('job_type')
        scheduled_date = request.form.get('scheduled_date')

        new_job = Job(
            customer_name=customer_name,
            technician_name=technician_name,
            job_type=job_type,
            scheduled_date=scheduled_date
        )
        db.session.add(new_job)
        db.session.commit()
        flash("New job added successfully!", "success")
        return redirect(url_for('home'))

    return render_template('create_job.html')

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
                job.before_photo_url = upload_to_cloudinary(before_photo)

            if after_photo:
                job.after_photo_url = upload_to_cloudinary(after_photo)

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
        return redirect(url_for('home'))

    before_photo_url = job.before_photo_url
    after_photo_url = job.after_photo_url

    return render_template('job_details.html', job=job, before_photo_url=before_photo_url, after_photo_url=after_photo_url)

# View All Jobs Route
@app.route('/view_jobs')
def view_jobs():
    jobs = Job.query.all()
    return render_template('view_jobs.html', jobs=jobs)

# Dashboard Route
@app.route('/dashboard')
def dashboard():
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

# Run the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
