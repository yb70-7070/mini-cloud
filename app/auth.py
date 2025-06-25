from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, UserMixin
from app import login_manager, bcrypt
from .db import get_connection
import mysql.connector


auth = Blueprint('auth', __name__)
users = {}  # temp in-memory store

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT USER_NAME FROM user WHERE USER_NAME = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return User(user_id)
    else:
        return None

@auth.route('/login', methods=['GET', 'POST'])
def login():
    result = None

    if request.method == 'POST':
        uid = request.form['username']
        pw = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT PASSWORD FROM user WHERE USER_NAME = %s", (uid,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

    if result is not None:
            stored_password_hash = result[0]
            if bcrypt.check_password_hash(stored_password_hash, pw):
                user = User(uid)
                login_user(user)
                return redirect(url_for('main.dashboard'))
    flash("Invalid login")

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uid = request.form['username']
        pw = request.form['password']
        pw_hash = bcrypt.generate_password_hash(pw).decode('utf-8')
       
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user (USER_NAME, PASSWORD) VALUES (%s, %s)", (uid, pw_hash))
            conn.commit()
            flash("Registered successfully")
            return redirect(url_for('auth.login'))
        except mysql.connector.errors.IntegrityError:
            flash("Username already exists")
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
