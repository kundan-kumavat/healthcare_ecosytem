from pymongo import MongoClient
from mongoengine import connect
from dotenv import load_dotenv
import os

load_dotenv()

mongo_client = os.getenv("MONGODB_CLIENT")
mongo_url = os.getenv("MONGODB_URL")

SECRET_KEY = os.getenv("SECRET_KEY")

# MongoDB Setup
client = MongoClient(mongo_client)
db = client['medical-data']
users_collection = db['users']
medical_collection = db['medical_data'] 
connect('medical-data', host=mongo_url)