import os
from werkzeug.utils import secure_filename
from flask import current_app

# Get the absolute path to the uploads folder
def get_user_folder(username):
    base = current_app.config['UPLOAD_FOLDER']
    user_folder = os.path.join(base, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

# Save an uploaded file
def save_file(file, username):
    if file:
        filename = secure_filename(file.filename)
        user_folder = get_user_folder(username)
        file_path = os.path.join(user_folder, filename)
        file.save(file_path)
        return filename
    return None

# List files uploaded by the user
def list_user_files(username):
    user_folder = get_user_folder(username)
    return os.listdir(user_folder)

# Get full path to a user's file for download
def get_file_path(username, filename):
    user_folder = get_user_folder(username)
    return os.path.join(user_folder, secure_filename(filename))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

import os

def get_user_storage_usage(user_id):
    user_folder = os.path.join('uploads', user_id)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(user_folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size  # in bytes
