from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from mongoengine import connect
from bson.objectid import ObjectId
from models import UserDocument, MedicalData, Appointment, Post, CommunityGroup, ChatBot
import datetime
from scraping import scrape_doctors
from datetime import datetime
from chatbot import chatbot
from config import SECRET_KEY, connect, db, users_collection, medical_collection, client


app = Flask(__name__, template_folder='templates', static_folder='staticFolder')
app.secret_key = SECRET_KEY

# Set up bcrypt for password hashing
bcrypt = Bcrypt(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

    @staticmethod
    def get(user_id):
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_id=user_data['_id'], username=user_data['username'])
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Check if username exists
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('register'))

        # Insert user into MongoDB
        users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password})
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/model')
@login_required
def model():
    return render_template('model.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find user in MongoDB
        user_data = users_collection.find_one({'username': username})
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_id=str(user_data['_id']), username=user_data['username'])
            login_user(user)
            flash('Login successful!', 'success')  # Flash success message
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'error')  # Flash error message
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    if request.method == 'POST':
        dateFiled = request.form['dateFiled']

        date_filed = datetime.strptime(dateFiled, '%Y-%m-%d')
        appointment = Appointment(
            doctor_name=request.form['doctor_name'],
            specialization=request.form['specialization'],
            location=request.form['location'],
            consultation_fee=request.form['consultation_fee'],
            clinic_name=request.form['clinic_name'],
            experience=request.form['experience'],
            appointment_date= dateFiled,
            user_id=current_user.id, # Using current_user ID
        )
        appointment.save()
        return redirect(url_for('reminder'))
    

@app.route('/notification')
def notification():
    return render_template('notifiaction.html')

# Home route
@app.route('/dashboard')
@login_required
def index():
    # Query the medical data for the current logged-in user
    medical_data_list = MedicalData.objects(user=current_user.id).all()  # Get all medical data for the current user

    # Convert medical data into a list or array
    medical_data_array = []
    for data in medical_data_list:
        medical_data_array.append({
            'first_name': data.first_name,
            'last_name': data.last_name,
            'age': data.age,
            'profession': data.profession,
            'gender': data.gender,
            'height': data.height,
            'weight': data.weigth,
            'previous_surgery_name': data.previous_surgery_name,
            'previous_surgery_date': data.previous_surgery_date,
            'complications_during_surgery': data.complications_during_surgery,
            'anestesia_history': data.anestesia_history,
            'chronic_conditions': data.chronic_conditions,
            'current_medications': data.current_medications,
            'known_allergies': data.known_allergies,
            'disease': data.disease,
            'drug_name': data.drug_name,
            'medication_duration': data.medication_duration,
            'addication_name': data.addication_name,
            'addication_frequency': data.addication_frequency,
            'addication_duration': data.addication_duration,
            'heart_rate': data.heart_rate,
            'blood_pressure': data.blood_pressure,
            'sugar_level': data.sugar_level,
            'diabetes_status': data.diabetes_status,
            'smartwatch_data': data.smartwatch_data,
            'medical_appointments': data.medical_appointments,
            'medical_reports': data.medical_reports,
            'diagnosis': data.diagnosis,
            'medicines_prescribed': data.medicines_prescribed,
            'created_at': data.created_at
        })

    # Pass the medical data array to the template
    return render_template('index.html', username=current_user.username, medical_data=medical_data_array)

@app.route('/upload', methods=["GET", "POST"])
@login_required
def upload():
    
    return render_template('report.html')

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/form')
def form():
    return render_template("form.html")

@app.route('/appointments')
@login_required
def get_appointments():
    user_appointments = Appointment.objects(user_id=current_user.id)  # Fetch only the current user's appointments

    # Format the appointments as events for FullCalendar
    events = []
    for appointment in user_appointments:
        events.append({
            'title': f'Appointment with {appointment.doctor_name}',
            'start': appointment.appointment_date.strftime('%Y-%m-%d'),
            'allDay': True  # Full-day event
        })

    return jsonify(events)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        profession = request.form['profession']
        working_hours = request.form['working_hours']
        gender = request.form['gender']
        height = request.form['height']
        weigth = request.form['weigth']
        previous_surgery_name = request.form['previous_surgery_name']
        previous_surgery_date = request.form['previous_surgery_date']
        complications_during_surgery = request.form['complications_during_surgery']
        anestesia_history = request.form['anestesia_history']
        chronic_conditions = request.form['chronic_conditions']
        current_medications = request.form['current_medications']
        known_allergies = request.form['known_allergies']
        disease = request.form['disease']
        drug_name = request.form['drug_name']
        medication_duration = request.form['medication_duration']
        addication_name = request.form['addication_name']
        addication_frequency = request.form['addication_frequency']
        addication_duration = request.form['addication_duration']

        medical_data = MedicalData(
            user=current_user.id,
            first_name = first_name,
            last_name = last_name,
            age = age,
            profession=profession,
            working_hours=working_hours,
            gender=gender,
            height=height ,
            weigth=weigth,
            previous_surgery_name=previous_surgery_name,
            previous_surgery_date=previous_surgery_date,
            complications_during_surgery=complications_during_surgery,
            anestesia_history=anestesia_history,
            chronic_conditions=chronic_conditions,
            current_medications=current_medications,
            known_allergies=known_allergies,
            disease=disease,
            drug_name=drug_name,
            medication_duration=medication_duration,
            addication_name=addication_name,
            addication_frequency=addication_frequency,
            addication_duration=addication_duration
        )
        medical_data.save()
        flash('Medical data added successfully', 'success')
        print('#####')
        print(current_user)
        return redirect(url_for('index', username=current_user.username))
    
    return render_template('profile.html')

@app.route('/calender')
@login_required
def calender():
    return render_template('calender.html')

@app.route('/chat', methods=["GET", "POST"])
@login_required
def chat():
    user_input = ''
    output = ''
    if request.method == "POST":
        user_input = request.form['user_input']
        response = chatbot(user_input)
        if response:
            output= response
        
        chat_record = ChatBot(
            owner=current_user.id,  # Stores current user's ID as owner
            user_input=user_input,
            output=output
        )

        chat_record.save()

    return render_template('chat.html', user_input=user_input, output=output)

# Wait for the page to load completely



@app.route('/search', methods=["GET", "POST"])
@login_required
def reminder():
    doctor_data = []  # Initialize doctor_data to avoid reference errors
    if request.method == "POST":
        specialist = request.form['specialist']
        location = request.form['location']
        
        # Ensure the scrape_doctors function is called with the correct parameters
        doctor_data = scrape_doctors(specialist=specialist, location=location)
        
        # Debug output to check if data is returned
        print(doctor_data)

    return render_template('appointmentdetails.html', doctor_data=doctor_data)

if __name__ == '__main__':
    app.run(debug=True)