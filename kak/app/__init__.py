# Import Flask and session from flask package
from flask import Flask, session
# Import Firebase Admin SDK components for authentication and database
from firebase_admin import credentials, initialize_app, firestore
# Import os for environment variable access
import os

# Define a function to create and configure our Flask application
def create_app():
    # Create a new Flask application instance
    app = Flask(__name__)
    
    # Set a secret key for session security
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize Firebase connection
    try:
        # Load Firebase credentials from the JSON file
        cred = credentials.Certificate('firebase-key.json')
        # Initialize the Firebase app with credentials and configuration
        firebase_app = initialize_app(cred, {
            # Set the storage bucket for Firebase Storage
            'storageBucket': 'roeeki-a4ca2.firebasestorage.app',
            # Set the database URL from environment variables
            'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', '')
        })
        
        # Create a Firestore database client
        db = firestore.client()
        
        # Reference to users collection in Firestore
        users_ref = db.collection('users')
        # Reference to tasks collection in Firestore
        tasks_ref = db.collection('tasks')
        # Reference to admins collection in Firestore
        admins_ref = db.collection('admins')
        
        # Create indexes for admin lookups
        # Note: In a production environment, this should be done through Firebase console
        # or using a deployment configuration, not during app initialization
        
        # Print success message when Firebase is properly initialized
        print("Firebase initialized successfully")
    # Catch any errors during Firebase initialization
    except Exception as e:
        # Print error message with details
        print(f"Error initializing Firebase: {e}")
        # Continue running the app even if Firebase fails
    
    # Import blueprints for different parts of the application
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    
    # Import models
    # This is not necessary here since models are imported where needed
    # but importing here ensures they're available throughout the app
    from app.models import User, Admin
    
    # Register the main blueprint for handling general routes
    app.register_blueprint(main_bp)
    # Register the authentication blueprint for login/signup
    app.register_blueprint(auth_bp)
    # Register the tasks blueprint for todo task management
    app.register_blueprint(tasks_bp)
    
    # Return the configured Flask application
    return app 