import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'YOUR_MONGODB_URI_HERE')
DB_NAME = os.getenv('DB_NAME', 'organ_donation_db')
SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

# Default admin credentials (created on first run if missing)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
