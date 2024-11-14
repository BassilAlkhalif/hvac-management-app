import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

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

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    technician_name = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    job_status = db.Column(db.String(50), default='scheduled')
    scheduled_date = db.Column(db.String(50))
    before_photo = db.Column(db.String(200))
    after_photo = db.Column(db.String(200))

if not os.path.exists('hvac_management.db'):
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

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
            if photo_type == 'before':
                job.before_photo = filepath
            else:
                job.after_photo = filepath
            db.session.commit()
            return jsonify({"message": f"{photo_type.capitalize()} photo uploaded successfully", "path": filepath})
        except Exception as e:
            return jsonify({"error": f"File upload failed: {str(e)}"}), 500

    return jsonify({"error": "Invalid upload"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
