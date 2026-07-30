from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-secret-key')
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grandmaster_tech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'instance/uploads/job_attachments'
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024


db = SQLAlchemy(app)

# ========== DATABASE MODELS ==========

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    company = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    equipment = db.relationship('Equipment', backref='customer', lazy=True)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    serial_number = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    job_cards = db.relationship('JobCard', backref='equipment', lazy=True)

class JobCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    problem_description = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    repair_process = db.Column(db.Text)
    parts_used = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')
    priority = db.Column(db.String(20), default='Normal')
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attachments = db.relationship(
        'JobAttachment',
        backref='job_card',
        lazy=True,
        cascade='all, delete-orphan'
    )

class JobAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(
        db.Integer,
        db.ForeignKey('job_card.id'),
        nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(100))
    category = db.Column(db.String(50), default='Other')
    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ========== ROUTES ==========

@app.route('/')
def dashboard():
    total_customers = Customer.query.count()
    total_equipment = Equipment.query.count()
    total_jobs = JobCard.query.count()
    pending_jobs = JobCard.query.filter_by(status='Pending').count()
    in_progress_jobs = JobCard.query.filter_by(status='In Progress').count()
    completed_jobs = JobCard.query.filter_by(status='Completed').count()
    
    recent_jobs = JobCard.query.order_by(JobCard.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
        total_customers=total_customers,
        total_equipment=total_equipment,
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        in_progress_jobs=in_progress_jobs,
        completed_jobs=completed_jobs,
        recent_jobs=recent_jobs)

@app.route('/customers')
def customers():
    all_customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customers/<int:id>')
def customer_detail(id):
    customer = Customer.query.get_or_404(id)
    return render_template('customer_detail.html', customer=customer)

@app.route('/customers/add', methods=['POST'])
def add_customer():
    customer = Customer(
        name=request.form['name'],
        phone=request.form['phone'],
        email=request.form['email'],
        company=request.form['company'],
        address=request.form['address']
    )
    db.session.add(customer)
    db.session.commit()
    flash('Customer added successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/equipment')
def equipment():
    all_equipment = Equipment.query.order_by(Equipment.created_at.desc()).all()
    customers = Customer.query.all()
    return render_template('equipment.html', equipment=all_equipment, customers=customers)

@app.route('/equipment/add', methods=['POST'])
def add_equipment():
    equipment = Equipment(
        customer_id=request.form['customer_id'],
        category=request.form['category'],
        brand=request.form['brand'],
        model=request.form['model'],
        serial_number=request.form['serial_number'],
        description=request.form['description']
    )
    db.session.add(equipment)
    db.session.commit()
    flash('Equipment added successfully!', 'success')
    return redirect(url_for('equipment'))


@app.route('/equipment/<int:id>')
def equipment_detail(id):
    equipment = Equipment.query.get_or_404(id)
    return render_template('equipment_detail.html', equipment=equipment)

@app.route('/jobcards')
def jobcards():
    all_jobs = JobCard.query.order_by(JobCard.created_at.desc()).all()
    equipment_list = Equipment.query.all()
    return render_template('jobcards.html', jobs=all_jobs, equipment=equipment_list)

@app.route('/jobcards/add', methods=['POST'])
def add_jobcard():
    job = JobCard(
        equipment_id=request.form['equipment_id'],
        title=request.form['title'],
        problem_description=request.form['problem_description'],
        priority=request.form['priority'],
        status='Pending'
    )
    db.session.add(job)
    db.session.commit()
    flash('Job Card created successfully!', 'success')
    return redirect(url_for('jobcards'))

@app.route('/jobcards/update/<int:id>', methods=['POST'])
def update_jobcard(id):
    job = JobCard.query.get_or_404(id)

    old_status = job.status
    new_status = request.form.get('status', 'Pending')

    job.title = request.form.get('title', '')
    job.problem_description = request.form.get('problem_description', '')
    job.diagnosis = request.form.get('diagnosis', '')
    job.repair_process = request.form.get('repair_process', '')
    job.parts_used = request.form.get('parts_used', '')
    job.status = new_status
    job.priority = request.form.get('priority', 'Normal')

    # Record the moment work starts
    if new_status == 'In Progress' and not job.started_at:
        job.started_at = datetime.utcnow()

    # Record the moment the repair is completed
    if new_status == 'Completed' and not job.completed_at:
        job.completed_at = datetime.utcnow()

    # Reopen a completed repair
    if old_status == 'Completed' and new_status == 'In Progress':
        job.completed_at = None

    # Reset workflow timestamps if returned to Pending
    if new_status == 'Pending':
        job.started_at = None
        job.completed_at = None

    db.session.commit()

    flash('Job Card updated successfully!', 'success')
    return redirect(url_for('jobcards'))


@app.route('/jobcards/<int:id>/attachments/upload', methods=['POST'])
def upload_job_attachment(id):
    job = JobCard.query.get_or_404(id)

    uploaded_file = request.files.get('file')
    category = request.form.get('category', 'Other')

    if not uploaded_file or not uploaded_file.filename:
        flash('Please select a file to upload.', 'error')
        return redirect(url_for('jobcards'))

    original_filename = uploaded_file.filename
    safe_filename = secure_filename(original_filename)

    if not safe_filename:
        flash('Invalid file name.', 'error')
        return redirect(url_for('jobcards'))

    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    stored_filename = f"{job.id}_{timestamp}_{safe_filename}"

    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    uploaded_file.save(os.path.join(upload_folder, stored_filename))

    attachment = JobAttachment(
        job_card_id=job.id,
        filename=stored_filename,
        original_filename=original_filename,
        file_type=uploaded_file.mimetype,
        category=category
    )

    db.session.add(attachment)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {
            'success': True,
            'message': 'Attachment uploaded successfully!',
            'attachment': {
                'id': attachment.id,
                'filename': attachment.filename,
                'original_filename': attachment.original_filename,
                'category': attachment.category,
                'file_type': attachment.file_type,
                'view_url': url_for('view_job_attachment', filename=attachment.filename),
                'download_url': url_for('download_job_attachment', filename=attachment.filename)
            }
        }

    flash('Attachment uploaded successfully!', 'success')
    return redirect(url_for('jobcards'))


@app.route('/jobcards/attachments/<path:filename>')
def view_job_attachment(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=False
    )


@app.route('/jobcards/attachments/<path:filename>/download')
def download_job_attachment(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )


@app.route('/jobcards/attachments/<int:attachment_id>/delete', methods=['POST'])
def delete_job_attachment(attachment_id):
    attachment = JobAttachment.query.get_or_404(attachment_id)

    file_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        attachment.filename
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(attachment)
    db.session.commit()

    flash('Attachment deleted successfully!', 'success')
    return redirect(url_for('jobcards'))


@app.route('/knowledge')
def knowledge():
    return render_template('knowledge.html')

# ========== INIT ==========

def initialize_database():
    with app.app_context():
        db.create_all()

initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
