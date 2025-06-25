from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, flash, current_app, abort
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from .storage import allowed_file, get_user_storage_usage  # helper function from storage.py
from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('auth.login'))

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.id)
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_size = len(file.read())
            file.stream.seek(0)
            current_usage = get_user_storage_usage(current_user.id)
            limit_bytes = 100 * 1024 * 1024
            if current_usage + file_size > limit_bytes:
                flash("Storage limit exceeded! You have used {:.2f} MB of 100 MB.".format(current_usage / (1024*1024)))
            else:
                file.save(os.path.join(user_folder, filename))
                flash(f"File '{filename}' uploaded successfully.")
        else:
            flash("Invalid file type.")


    query = request.args.get('q', '').lower()

    files = []
    
    for f in os.listdir(user_folder):
        if query in f.lower():  # partial case-insensitive search
            files.append({
                "name": f,
                "size": os.path.getsize(os.path.join(user_folder, f)) // 1024
            })
    current_usage = get_user_storage_usage(current_user.id)
    current_usage_mb = current_usage / (1024 * 1024)
    return render_template('dashboard.html', files=files, usage=current_usage_mb)

@main.route('/download/<filename>')
@login_required
def download(filename):
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.id)
    return send_from_directory(user_folder, secure_filename(filename), as_attachment=True)

@main.route('/preview/<filename>')
@login_required
def preview(filename):
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.id)
    file_path = os.path.join(user_folder, secure_filename(filename))

    if not os.path.exists(file_path):
        abort(404)

    ext = filename.rsplit('.', 1)[-1].lower()

    if ext in ['jpg', 'jpeg', 'png', 'gif']:
        return render_template('preview_image.html', filename=filename)
    elif ext == 'pdf':
        return render_template('preview_pdf.html', filename=filename)
    else:
        flash("Preview not supported for this file type.")
        return redirect(url_for('main.dashboard'))

@main.route('/userfile/<filename>', methods=['GET', 'POST'])
@login_required
def serve_file(filename):
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.id)
    return send_from_directory(user_folder, secure_filename(filename))

@main.route('/delete/<filename>', methods=['POST'])
@login_required
def delete(filename):
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.id)
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        flash("File not found.")
        return redirect(url_for('main.dashboard'))

    try:
        os.remove(file_path)
        flash(f"{filename} deleted successfully.")
    except Exception as e:
        flash(f"Error deleting file: {e}")

    return redirect(url_for('main.dashboard'))

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app.db import get_connection
    import os

    message = None
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.id)
    os.makedirs(user_folder, exist_ok=True)

    # Calculate file stats
    files = os.listdir(user_folder)
    total_files = len(files)
    total_size_bytes = sum(os.path.getsize(os.path.join(user_folder, f)) for f in files)
    total_size_mb = total_size_bytes / (1024 * 1024)  # convert to MB

    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        if not current_pw or not new_pw or not confirm_pw:
            message = "All password fields are required."
        elif new_pw != confirm_pw:
            message = "New passwords do not match."
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT PASSWORD FROM user WHERE USER_NAME = %s", (current_user.id,))
            result = cursor.fetchone()

            if result and bcrypt.check_password_hash(result[0], current_pw):
                new_pw_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
                cursor.execute("UPDATE user SET PASSWORD = %s WHERE USER_NAME = %s", (new_pw_hash, current_user.id))
                conn.commit()
                message = "Password updated successfully."
            else:
                message = "Current password is incorrect."

            cursor.close()
            conn.close()

    return render_template('profile.html', message=message, username=current_user.id,
                           total_files=total_files, total_size_mb=total_size_mb)
