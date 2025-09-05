
import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blogs.main import create_app, db
from blogs.main.models import Users
from blogs.main import bcrypt

def create_admin():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = Users.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"Admin account already exists: {existing_admin.username}")
            return
        
        # Get admin details
        print("Creating admin account...")
        username = input("Enter admin username: ")
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        first_name = input("Enter first name: ")
        last_name = input("Enter last name (optional): ")
        
        # Validate password (basic check)
        if len(password) < 8:
            print("Password must be at least 8 characters long")
            return
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create admin user
        admin_user = Users(
            username=username,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role='admin'
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin account created successfully: {username}")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin account: {str(e)}")

if __name__ == "__main__":
    create_admin() 