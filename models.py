from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField, EmbeddedDocumentField, FloatField, FileField
from datetime import datetime

# MongoEngine User model
class UserDocument(Document):
    username = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    profile_picture = FileField()
    friends = ListField(ReferenceField('self'))
    groups_joined = ListField(ReferenceField('CommunityGroup'))
    registration_date = DateTimeField(default=datetime.utcnow)

class PersonalData(Document):
    user=ReferenceField(UserDocument, required=True)
    first_name = StringField()
    last_name = StringField()
    date_of_birth = DateTimeField()
    phone_no = StringField()
    profession = StringField()
    gender = StringField()
    working_hours = StringField()
    height = StringField()
    weigth = StringField()
    address = StringField()
    country = StringField()
    city = StringField()
    region = StringField()
    postal_code = StringField()

class PastSurgeryInfo(Document):
    user = ReferenceField(UserDocument, required=True)
    pervious_surgery_name = StringField()
    pervious_surgery_date = DateTimeField()
    compliactions = StringField()
    anstesia_history = StringField()

class CurrentMedication(Document):
    user = ReferenceField(UserDocument, required=True)
    disease_name = StringField()
    current_medicines  = StringField()
    current_medication_duration = StringField()
    known_allergies = StringField()

class Addication(Document):
    user = ReferenceField(UserDocument, required=True)
    addication_name = StringField()
    frequency = StringField()
    addication_duration = StringField()


# Medical Data Collection Schema
class MedicalData(Document):
    user = ReferenceField(UserDocument, required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    age = StringField()
    profession = StringField()
    working_hours = StringField()
    gender = StringField()
    height = StringField()
    weigth = StringField()
    previous_surgery_name  = StringField()
    previous_surgery_date = DateTimeField()
    complications_during_surgery = StringField()
    anestesia_history = StringField()
    chronic_conditions= StringField()
    current_medications= StringField()
    known_allergies = StringField()
    disease = StringField()
    drug_name = StringField()
    medication_duration = StringField()
    addication_name = StringField()
    addication_frequency = StringField()
    addication_duration = StringField()
    heart_rate = FloatField()  # Beats per minute (BPM)
    blood_pressure = StringField()  # E.g., "120/80 mmHg"
    sugar_level = FloatField()  # Blood sugar level
    diabetes_status = StringField(choices=["No", "Pre-diabetes", "Diabetes"])
    smartwatch_data = ListField(StringField())  # Data synced from smartwatch
    medical_appointments = ListField(StringField())  # List of appointment dates
    medical_reports = ListField(FileField())  # Medical reports (scanned files or PDFs)
    diagnosis = StringField()  # Diagnosis details
    medicines_prescribed = ListField(StringField())  # List of medicines
    created_at = DateTimeField(default=datetime.utcnow)

# Community Group Schema
class CommunityGroup(Document):
    group_name = StringField(required=True, unique=True)
    description = StringField()
    created_by = ReferenceField(UserDocument)
    group_members = ListField(ReferenceField(UserDocument))
    profile_picture = FileField()
    created_at = DateTimeField(default=datetime.utcnow)

# Post Schema
class Post(Document):
    content = StringField(required=True)
    posted_by = ReferenceField(UserDocument, required=True)
    posted_on_group = ReferenceField(CommunityGroup, required=True)
    created_at = DateTimeField(default=datetime.utcnow)

class ChatBot(Document):
    owner = ReferenceField(UserDocument)
    user_input = StringField()
    output = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)

class Appointment(Document):
    doctor_name = StringField(required=True)
    specialization = StringField(required=True)
    location = StringField(required=True)
    consultation_fee = StringField(required=True)
    clinic_name = StringField(required=True)
    experience = StringField(required=True)
    user_id = ReferenceField(UserDocument)
    appointment_date = DateTimeField(required=True)