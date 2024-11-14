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
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
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
     
