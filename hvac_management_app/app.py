import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hvac_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "123456"

# Absolute path for uploads folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

db = SQLAlchemy(app)

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Models
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
            if 'upload_before' in request.form:
                before_photo = request.files['before_photo']
                if before_photo:
                    filename = secure_filename(before_photo.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    before_photo.save(filepath)
                    job.before_photo = filename
                    db.session.commit()
                    flash("Before photo uploaded successfully!", "success")
                    return redirect(url_for('perform_job', job_id=job_id))

            elif 'upload_after' in request.form:
                after_photo = request.files['after_photo']
                comment = request.form.get('comment')
                if after_photo:
                    filename = secure_filename(after_photo.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    after_photo.save(filepath)
                    job.after_photo = filename
                    job.notes = comment
                    job.job_status = 'completed'
                    job.completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    db.session.commit()
                    flash("Job completed successfully!", "success")
                    return redirect(url_for('home'))

        return render_template('perform_job.html', job=job)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('home'))

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
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('home'))

# View All Jobs Route
@app.route('/view_jobs')
def view_jobs():
    try:
        jobs = Job.query.all()
        if not jobs:
            flash("No jobs found!", "info")
        return render_template('view_jobs.html', jobs=jobs)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('home'))

# Job Details Route
@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    job = Job.query.get(job_id)
    if not job:
        flash("Job not found!", "danger")
        return redirect(url_for('view_jobs'))
    return render_template('job_details.html', job=job)

# Run the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
