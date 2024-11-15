import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import time
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hvac_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "123456"

# Cloudinary configuration
cloudinary.config(
    cloud_name="dc3tb4drj",
    api_key="189685417282461",
    api_secret="vOCqr2HynRmmODmLm9Mz_Xl4W9I"
)

db = SQLAlchemy(app)

# Ensure the uploads folder exists
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
    before_photo = db.Column(db.String(200))
    after_photo = db.Column(db.String(200))
    completion_time = db.Column(db.String(50))
    notes = db.Column(db.String(500))

# Initialize the database
if not os.path.exists('hvac_management.db'):
    with app.app_context():
        db.create_all()

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
            timestamp = str(int(time.time()))

            # Upload before photo
            if before_photo:
                try:
                    upload_result = cloudinary.uploader.upload(
                        before_photo,
                        timestamp=timestamp,
                        api_key="189685417282461",
                        api_secret="vOCqr2HynRmmODmLm9Mz_Xl4W9I"
                    )
                    job.before_photo = upload_result['secure_url']
                except Exception as e:
                    logging.error(f"Before photo upload failed: {str(e)}")
                    flash("Before photo upload failed.", "danger")

            # Upload after photo
            if after_photo:
                try:
                    upload_result = cloudinary.uploader.upload(
                        after_photo,
                        timestamp=timestamp,
                        api_key="189685417282461",
                        api_secret="vOCqr2HynRmmODmLm9Mz_Xl4W9I"
                    )
                    job.after_photo = upload_result['secure_url']
                except Exception as e:
                    logging.error(f"After photo upload failed: {str(e)}")
                    flash("After photo upload failed.", "danger")

            # Update job status
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

# Dashboard Route with Charts
@app.route('/dashboard')
def dashboard():
    try:
        total_jobs = Job.query.count()
        completed_jobs = Job.query.filter_by(job_status='completed').count()
        pending_jobs = total_jobs - completed_jobs

        technician_data = db.session.query(Job.technician_name, db.func.count(Job.id)).group_by(Job.technician_name).all()
        technician_names = [data[0] for data in technician_data]
        technician_counts = [data[1] for data in technician_data]

        return render_template(
            'dashboard.html',
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            pending_jobs=pending_jobs,
            technician_names=technician_names,
            technician_counts=technician_counts
        )
    except Exception as e:
        logging.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('home'))

# Run the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
