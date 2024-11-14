import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
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

# Path for uploads folder (inside 'static' for Flask static file serving)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
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

        try:
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
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
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
            # Handle Before Photo Upload
            if 'upload_before' in request.form:
                before_photo = request.files['before_photo']
                if before_photo:
                    filename = f"{job_id}_before_{int(time.time())}_{secure_filename(before_photo.filename)}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    before_photo.save(filepath)
                    logging.debug(f"Before photo saved at: {filepath}")
                    if os.path.exists(filepath):
                        logging.debug("Before photo file exists.")
                    else:
                        logging.error("Before photo file does not exist after saving.")
                    job.before_photo = filename
                    db.session.commit()
                    flash("Before photo uploaded successfully!", "success")
                    return redirect(url_for('perform_job', job_id=job_id))

            # Handle After Photo Upload
            elif 'upload_after' in request.form:
                after_photo = request.files['after_photo']
                comment = request.form.get('comment')
                if after_photo:
                    filename = f"{job_id}_after_{int(time.time())}_{secure_filename(after_photo.filename)}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    after_photo.save(filepath)
                    logging.debug(f"After photo saved at: {filepath}")
                    if os.path.exists(filepath):
                        logging.debug("After photo file exists.")
                    else:
                        logging.error("After photo file does not exist after saving.")
                    job.after_photo = filename
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
    try:
        job = Job.query.get(job_id)
        if not job:
            flash("Job not found!", "danger")
            return redirect(url_for('view_jobs'))

        before_photo_url = url_for('static', filename=f'uploads/{job.before_photo}') if job.before_photo else None
        after_photo_url = url_for('static', filename=f'uploads/{job.after_photo}') if job.after_photo else None

        return render_template('job_details.html', job=job, before_photo_url=before_photo_url, after_photo_url=after_photo_url)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('view_jobs'))

# Run the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
