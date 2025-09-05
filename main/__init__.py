from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os import path
from flask_jwt_extended import JWTManager
import os

# Initialize extensions first
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
DB_NAME = "blog_store"

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    db.init_app(app)
    jwt.init_app(app)

    # Import blueprints after db is defined
    from .auth import auth
    from .post import post
    from .comment import comment
    
    app.register_blueprint(auth, url_prefix = '/auth')
    app.register_blueprint(post, url_prefix = '/post')
    app.register_blueprint(comment, url_prefix = '/comment')

    with app.app_context():
        db.create_all()

    return app
