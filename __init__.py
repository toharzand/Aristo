from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import timedelta

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,template_folder='templates',static_folder=r'C:\Users\itay dar\Desktop\פרויקטים\tender\hello_flask\git checker\aristo\templates')

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://itda:28031994@127.0.0.1:3306/new_tender'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.secret_key = "AristoSecretKeyHashing"
    app.permanent_session_lifetime = timedelta(minutes=5)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User


