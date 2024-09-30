from pymongo import MongoClient
from mongoengine import connect

SECRET_KEY = 'KUNDAN1234'

# MongoDB Setup
client = MongoClient("mongodb+srv://kundankumawat003:kundan1234@cluster0.7hqin.mongodb.net/")
db = client['medical-data']
users_collection = db['users']
medical_collection = db['medical_data'] 
connect('medical-data', host="mongodb+srv://kundankumawat003:kundan1234@cluster0.7hqin.mongodb.net/medical-data")