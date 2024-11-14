import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hvac_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    jobs = Job.query.filter_by(job_status="scheduled").all()
    return render_template('index.html', jobs=jobs)

# Create New Job Route
@app.route('/create_job', methods=['POST'])
def create_job():
    customer_name = request.form.get('customer_name')
    technician_name = request.form.get('technician_name')
    job_type = request.form.get('job_type')
    if job_type == "Repair":
        job_type = "Maintenance"  # Combine Repair and Maintenance
    scheduled_date = request.form.get('scheduled_date')

    try:
        new_job = Job(
            customer_name=customer_name,
            technician_name=technician_name,
            job_type=job_type,
            job_status='scheduled',
            scheduled_date=scheduled_date
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('home'))
    except Exception as e:
        return jsonify({"error": f"Job creation failed: {str(e)}"}), 500

# Complete Job Route
@app.route('/complete_job', methods=['POST'])
def complete_job():
    job_id = request.form.get('job_id')
    photo_type = request.form.get('photo_type')
    file = request.files['file']
    notes = request.form.get('notes')

    if file and photo_type in ['before', 'after']:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)
            job = Job.query.get(job_id)

            if not job:
                return jsonify({"error": f"Job with ID {job_id} not found"}), 404

            if photo_type == 'before':
                job.before_photo = filepath
            else:
                job.after_photo = filepath

            job.job_status = 'completed'
            job.completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            job.notes = notes

            db.session.commit()
            return jsonify({"message": f"Job {job_id} marked as completed with {photo_type} photo uploaded", "path": filepath})
        except Exception as e:
            return jsonify({"error": f"File upload failed: {str(e)}"}), 500

    return jsonify({"error": "Invalid upload"}), 400

# View All Jobs Route
@app.route('/view_jobs')
def view_jobs():
    jobs = Job.query.all()
    return render_template('view_jobs.html', jobs=jobs)

# Job Details Route
@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": f"Job with ID {job_id} not found"}), 404
    return render_template('job_details.html', job=job)

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    # Get total job count
    total_jobs = Job.query.count()

    # Get count of completed and pending jobs
    completed_jobs = Job.query.filter_by(job_status='completed').count()
    pending_jobs = total_jobs - completed_jobs

    # Get job count per technician
    technician_data = db.session.query(Job.technician_name, db.func.count(Job.id)).group_by(Job.technician_name).all()
    technician_names = [data[0] for data in technician_data]
    technician_counts = [data[1] for data in technician_data]

    # Data for charts
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
    app.run(host='0.0.0.0', port=5000)
