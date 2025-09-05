from flask import Blueprint, request, jsonify, render_template
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from .models import Users
from . import db, bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import re

auth = Blueprint('auth', __name__)


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[\W_]', password):
        return False
    return True


@auth.route('/sign_up/', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST' :
            required_fields = ['username', 'email', 'password', 'first_name']

            user_required_data = {
                "username": request.form.get("username"),
                "email": request.form.get("email"),
                "password": request.form.get("password"),
                "first_name": request.form.get("first_name"),
            }

            user_optional_data = {
                "last_name": request.form.get("last_name")
            }

            missing_fields = [field for field in required_fields if not user_required_data.get(field)]
            if missing_fields:
                return jsonify(
                    {"message": f"Missing required fields: {', '.join(missing_fields)}",
                    "status": "error"}
                    ), 400

            if not is_valid_email(user_required_data['email']):
                return jsonify(
                    {"message": "Invalid email format",
                    "status": "error",}
                    ), 400
            
            if not is_valid_password(user_required_data['password']):
                return jsonify(
                    {"message": "Invalid password format,need to have atleast "
                    "uppercase letter,special characters,lowercase,length must "
                    "be greater than 8",
                    "status": "error"
                }),400

            hashed_password = bcrypt.generate_password_hash(user_required_data['password']).decode('utf-8')

            new_user = Users(
                    username= user_required_data['username'],
                    email= user_required_data['email'], 
                    password=  hashed_password,
                    first_name = user_required_data['first_name'],
                    last_name = user_optional_data['last_name'],
                    role = 'user'  # Explicitly set role as user for regular signup
                )

            db.session.add(new_user)
            db.session.commit()
            return jsonify(
                {"message": "Successfully registered",
                "status": "success"}
                ), 200
        
        elif request.method == 'GET':
            return jsonify(
                {"message": "Need to Signup",
                "status": "pending"}
                ),202
    
    except IntegrityError:

        db.session.rollback()
        return jsonify({"message":"Username already exists","status":"error"}), 400

        

@auth.route('/login/', methods=['POST'])
def login():

        if request.method == 'POST':
            required_fields = ['username', 'password']
            user_data = {
                "username" : request.form.get("username"),
                "password" :   request.form.get("password")
            }

            missing_fields = [field for field in required_fields if not user_data.get(field)]
            if missing_fields:
                return jsonify(
                    {"message": f"Missing required fields: {', '.join(missing_fields)}",
                    "status": "error"}), 400

            else:
                user = Users.query.filter_by(username=user_data['username']).first()
                
                if user and bcrypt.check_password_hash(user.password, user_data['password']):
                        access_token = create_access_token(identity = user.user_id, expires_delta=timedelta(hours=24))
                        refresh_token = create_refresh_token(identity = user.user_id, expires_delta=timedelta(days=7))

                        redirect_url = '/post/view_post/'

                        return jsonify({
                                        "message":"Successfully logged in",
                                        "user": {
                                            "user_id": user.user_id,
                                            "username": user.username,
                                            "email": user.email,
                                            "first_name": user.first_name,
                                            "last_name": user.last_name,
                                            "role": user.role
                                        },
                                        "tokens": {
                                                "access_token": access_token,
                                                "refresh_token": refresh_token,
                                                "url_for_posts": redirect_url
                                                },
                                        "status":"success"
                                    }), 200
                
                
                return jsonify(
                    {"message":"Username or password is invalid",
                    "status":"error"}), 400
                

@auth.route('/login-page/', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth.route('/signup-page/', methods=['GET'])
def signup_page():
    return render_template('signup.html')   


@auth.route('/create-admin/', methods=['POST', 'GET'],)
def create_admin():
    try:
        if request.method == 'POST':
            required_fields = ['username', 'email', 'password', 'first_name']

            admin_data = {
                "username": request.form.get("username"),
                "email": request.form.get("email"),
                "password": request.form.get("password"),
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name")
            }

            missing_fields = [field for field in required_fields if not admin_data.get(field)]
            if missing_fields:
                return jsonify(
                    {"message": f"Missing required fields: {', '.join(missing_fields)}",
                    "status":"error"}), 400

            if not is_valid_email(admin_data['email']):
                return jsonify(
                    {"message": "Invalid email format",
                    "status": "error"}), 400
            
            if not is_valid_password(admin_data['password']):
                return jsonify(
                    {"message": "Invalid password format,need to have atleast uppercase "
                    "letter,special characters,lowercase,length must be greater "
                    "than 8",
                    "status": "error"}), 400

            # Check if admin already exists
            email = request.form.get("email")
            existing_admin = Users.query.filter_by(role='admin', email=email).first()
            if existing_admin:
                return jsonify({"message": "Admin account already exists", "status": "error"}), 400

            hashed_password = bcrypt.generate_password_hash(admin_data['password']).decode('utf-8')

            new_admin = Users(
                username=admin_data['username'],
                email=admin_data['email'], 
                password=hashed_password,
                first_name=admin_data['first_name'],
                last_name=admin_data['last_name'],
                role='admin'
            )

            db.session.add(new_admin)
            db.session.commit()
            return jsonify(
                {"message": "Admin account created successfully",
                "status": "success"}
                ), 200
        if request.method == 'GET':
            return render_template('create_admin.html')

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message":"Username or email already exists","status":"error"}), 400


@auth.route('/get-user-info/', methods=['GET'])
@jwt_required()
def get_user_info():
    """
    Get current user information including role
    """
    current_user_id = get_jwt_identity()
    user = Users.query.filter_by(user_id=current_user_id).first()
    
    if not user:
        return jsonify({"message": "User not found", "status": "error"}), 404
    
    return jsonify({
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_admin": user.is_admin(),
            "is_user": user.is_user()
        },
        "status": "success"
    }), 200


@auth.route('/logout/',methods=['GET'])
@jwt_required()
def logout():
    return jsonify({"status":"Success","message":"Succesfully logout"}), 201


    