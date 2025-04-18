from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from mongoengine import connect
from bson.objectid import ObjectId
from models import UserDocument, MedicalData, Appointment, Post, CommunityGroup, ChatBot, PersonalData, PastSurgeryInfo, CurrentMedication, Addication
import datetime
from scraping import scrape_doctors
from datetime import datetime
from chatbot import chatbot
from config import SECRET_KEY, connect, db, users_collection, medical_collection, client
import os
from cbc_daigonse import daigonse

app = Flask(__name__, template_folder='templates', static_folder='staticFolder')
app.secret_key = SECRET_KEY

UPLOAD_FOLDER = 'staticFolder/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        timeFiled = request.form['timeSlot']

        date_filed = datetime.strptime(dateFiled, '%Y-%m-%d')
        appointment = Appointment(
            doctor_name=request.form['doctor_name'],
            specialization=request.form['specialization'],
            location=request.form['location'],
            consultation_fee=request.form['consultation_fee'],
            clinic_name=request.form['clinic_name'],
            experience=request.form['experience'],
            appointment_date= dateFiled,
            time_slot = timeFiled,
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
    # personal_data_list = PersonalData.objects(user=current_user.id).all()  # Get all medical data for the current user

    # Convert medical data into a list or array
    # personal_data_array = []
    # for data in personal_data_list:
    #     personal_data_array.append({
    #         'first_name': data.first_name,
    #         'last_name': data.last_name,
    #         'profession': data.profession,
    #         'gender': data.gender,
    #         'height': data.height,
    #         'weight': data.weigth,
    #     })

    # Pass the medical data array to the template
    return render_template('dashboard.html', username=current_user.username)

@app.route('/dash')
def dash():
    return render_template('dashboard.html')

@app.route('/upload', methods=["GET", "POST"])
@login_required
def upload():
    if request.method == 'POST':
        cbc_file = request.files.get("cbc_report")
        xray_file = request.files.get("xray_report")

        # file = request.files['file']

        if cbc_file and cbc_file.filename != "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], cbc_file.filename)
            cbc_file.save(file_path)
            print(f"Attempting to save file to: {file_path}")

            model_output = model_output = daigonse(file_path)
            return render_template('report.html', output = model_output)

        elif xray_file and xray_file.filename != "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], xray_file.filename)
            xray_file.save(file_path)
            print(f"Attempting to save file to: {file_path}")

            model_output = model_output = daigonse(file_path)
            return render_template('report.html', output = model_output)

        else:
            # Call the model function with the file path
            model_output = 'No file uploaded'
            return render_template('report.html', output = model_output)
    
    return render_template('report.html')

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/drugs')
def drugs():
    return render_template('drugs.html')

@app.route('/global-data')
def global_indicator():
    return render_template('globalIndicator.html')

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
    # Query the medical data for the current logged-in user
    personal_data_list = PersonalData.objects(user=current_user.id).all()  # Get all medical data for the current user

    # Convert medical data into a list or array
    personal_data_array = []
    for data in personal_data_list:
        personal_data_array.append({
            'first_name': data.first_name,
            'last_name': data.last_name,
            'profession': data.profession,
            'gender': data.gender,
            'height': data.height,
            'weight': data.weigth,
            'dob': data.date_of_birth,
            'phone_no': data.phone_no,
            'working_hours': data.working_hours,
            'address': data.address,
            'address_2': data.address_2,
            'country': data.country,
            'city': data.city,
            'region': data.region,
            'postal_code': data.postal_code
        })
    return render_template('profile.html', personal_data_array=personal_data_array)

@app.route('/calender')
@login_required
def calender():
    return render_template('calender.html')

@app.route('/chat', methods=["GET", "POST"])
@login_required
def chat():
    user_input = ''
    output = ''

    chat_history = ChatBot.objects(owner=current_user.id).order_by("+timestamp")

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
    
    chat_history = ChatBot.objects(owner=current_user.id).order_by("+timestamp")

    return render_template('chat.html', output=output, chat_history=chat_history)

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

@app.route('/personalData', methods=['GET', 'POST'])
def personalData():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_no = request.form['phone_no']
        date_of_birth = request.form['date_of_birth']
        profession = request.form['profession']
        gender = request.form['gender']
        working_hours = request.form['working_hours']
        height = request.form['height']
        weigth = request.form['weigth']
        address = request.form['address']
        address_2 = request.form['address_2']
        city = request.form['city']
        region = request.form['region']
        postal_code = request.form['postal_code']

        personal_data = PersonalData(
            user=current_user.id,
            first_name = first_name,
            last_name = last_name,
            phone_no = phone_no,
            date_of_birth = date_of_birth,
            profession = profession,
            gender = gender,
            working_hours = working_hours,
            height = height,
            weigth = weigth,
            address = address,
            address_2 = address_2,
            city = city,
            region =  region,
            postal_code =  postal_code,
        )
        personal_data.save()
        flash("Personal Data saved successfully", 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/pastSurgicalData', methods=['GET', 'POST'])
def pastSurgicalData():
    if request.method == 'POST':
        pervious_surgery_name = request.form['pervious_surgery_name']
        pervious_surgery_date = request.form['pervious_surgery_date']
        compliactions = request.form['compliactions']
        anstesia_history = request.form['anstesia_history']

        past_surgical_data = PastSurgeryInfo(
            user=current_user.id,
            pervious_surgery_name = pervious_surgery_name,
            pervious_surgery_date  = pervious_surgery_date ,
            compliactions = compliactions,
            anstesia_history = anstesia_history,
        )
        past_surgical_data.save()
        flash("Personal Data saved successfully", 'success')
    
    return render_template('profile.html')

@app.route('/currentMedication', methods=['GET', 'POST'])
def currentMedication():
    if request.method == 'POST':
        disease_name = request.form['disease_name']
        current_medicines = request.form['current_medicines']
        current_medication_duration = request.form['current_medication_duration']
        known_allergies = request.form['known_allergies']

        current_medication_data = CurrentMedication(
            user=current_user.id,
            disease_name = disease_name,
            current_medicines  = current_medicines ,
            current_medication_duration = current_medication_duration,
            known_allergies = known_allergies,
        )
        current_medication_data.save()
        flash("Personal Data saved successfully", 'success')
    
    return render_template('profile.html')

@app.route('/addication', methods=['GET', 'POST'])
def addication():
    if request.method == 'POST':
        addication_name = request.form['addication_name']
        frequency = request.form['frequency']
        addication_duration = request.form['addication_duration']

        addication_data = Addication(
            user=current_user.id,
            addication_name = addication_name,
            frequency  = frequency ,
            addication_duration = addication_duration,
        )
        addication_data.save()
        flash("Personal Data saved successfully", 'success')
    
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)