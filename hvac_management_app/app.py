import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hvac_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Use an absolute path for the uploads folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

db = SQLAlchemy(app)

# Ensure the uploads directory exists
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

# Initialize the database and add dummy jobs for testing
if not os.path.exists('hvac_management.db'):
    with app.app_context():
        db.create_all()
        if Job.query.count() == 0:  # Only add dummy jobs if the table is empty
            dummy_jobs = [
                Job(customer_name="Alice", technician_name="John", job_type="Installation", job_status="scheduled", scheduled_date="2024-11-15"),
                Job(customer_name="Bob", technician_name="Jane", job_type="Maintenance", job_status="scheduled", scheduled_date="2024-11-16"),
                Job(customer_name="Charlie", technician_name="Mike", job_type="Repair", job_status="scheduled", scheduled_date="2024-11-17"),
            ]
            db.session.add_all(dummy_jobs)
            db.session.commit()

# Home Route
@app.route('/')
def home():
    jobs = Job.query.filter_by(job_status="scheduled").all()
    return render_template('index.html', jobs=jobs)

# Create Job Route
@app.route('/create_job', methods=['POST'])
def create_job():
    customer_name = request.form.get('customer_name')
    technician_name = request.form.get('technician_name')
    job_type = request.form.get('job_type')
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

# Upload Photo Route
@app.route('/upload', methods=['POST'])
def upload_photo():
    job_id = request.form.get('job_id')
    photo_type = request.form.get('photo_type')
    file = request.files['file']

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

            db.session.commit()
            return jsonify({"message": f"{photo_type.capitalize()} photo uploaded successfully", "path": filepath})
        except Exception as e:
            return jsonify({"error": f"File upload failed: {str(e)}"}), 500

    return jsonify({"error": "Invalid upload"}), 400

# Run the Application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
