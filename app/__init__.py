from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os

login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx'}
    app.config['STORAGE_LIMIT_MB'] = 100 
    bcrypt.init_app(app)

    login_manager.init_app(app)
    bcrypt.init_app(app)

    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    return app
