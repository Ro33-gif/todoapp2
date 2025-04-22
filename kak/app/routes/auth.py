# Import required components from Flask
from flask import Blueprint, request, jsonify, session
# Import Firebase authentication, database and storage
from firebase_admin import auth, firestore, storage
# Import secure_filename to sanitize uploaded file names
from werkzeug.utils import secure_filename
# Import UUID for generating unique identifiers
import uuid
# Import tempfile for creating temporary files
import tempfile
# Import os for file operations
import os
# Import datetime for handling dates and times
from datetime import datetime
# Import User and Admin models
from app.models import User, Admin

# Create a Blueprint for auth routes with prefix '/auth'
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
# Create a Firestore database client
db = firestore.client()
# Get reference to Firebase storage bucket
bucket = storage.bucket()

# Define function to check if user is authenticated
def check_auth():
    """Check if user is authenticated"""
    # Get user ID from session
    user_id = session.get('user_id')
    # If no user ID found, user is not authenticated
    if not user_id:
        return False, {'error': 'Authentication required'}, 401
    # If user ID found, user is authenticated
    return True, user_id, None

# Define function to check if user is an admin
def check_admin():
    """Check if user is admin"""
    # Get user ID from session
    user_id = session.get('user_id')
    # Get admin status from session
    is_admin = session.get('is_admin')
    
    # If no user ID found, user is not authenticated
    if not user_id:
        return False, None, {'error': 'Authentication required', 'code': 401}
    
    # Check for admin status
    if not is_admin:
        # If not admin in session, check for admin record
        admin = Admin.get_by_user_id(user_id)
        if admin:
            # Update session with admin status
            session['is_admin'] = True
            # Return that user is admin
            return True, user_id, None
                
        # If not admin, return error
        return False, None, {'error': 'Admin privileges required', 'code': 403}
        
    # If admin, return success
    return True, user_id, None

# Define route for user registration
@auth_bp.route('/register', methods=['POST'])
# Define the function that handles registration requests
def register():
    """Register a new user"""
    try:
        # Get JSON data from request
        data = request.json
        # Get email from request data
        email = data.get('email')
        # Get password from request data
        password = data.get('password')
        
        # Create user in Firebase Authentication
        firebase_user = auth.create_user(
            email=email,
            password=password
        )
        
        # Create user model
        user = User(
            uid=firebase_user.uid,
            email=email,
            task_count=0,
            last_active=datetime.now().isoformat()
        )
        
        # Save user to Firestore
        user.save()
        
        # Return success message and user ID
        return jsonify({'message': 'User registered successfully', 'userId': user.uid}), 201
    # Catch any exceptions during registration
    except Exception as e:
        # Return error message
        return jsonify({'error': str(e)}), 400

# Define route for user login
@auth_bp.route('/login', methods=['POST'])
# Define the function that handles login requests
def login():
    """Login route - frontend will handle actual Firebase Auth"""
    # This endpoint is mainly for session management on backend
    try:
        # Get JSON data from request
        data = request.json
        # Get ID token from request data
        id_token = data.get('idToken')  # Firebase Auth ID token
        
        # Check if ID token is provided
        if not id_token:
            # Return error if no token provided
            return jsonify({'error': 'No ID token provided'}), 400
        
        # Verify the ID token
        try:
            # Decode and verify the token
            decoded_token = auth.verify_id_token(id_token)
            # Get user ID from token
            uid = decoded_token['uid']
        # Catch token verification errors
        except Exception as e:
            # Return error if token is invalid
            return jsonify({'error': f'Invalid ID token: {str(e)}'}), 401
        
        # Get user from User model
        user = User.get_by_id(uid)
        
        # If user doesn't exist in database, create it
        if not user:
            # Get user info from Firebase Auth
            firebase_user = auth.get_user(uid)
            # Create new User model
            user = User(
                uid=uid,
                email=firebase_user.email,
                task_count=0,
                last_active=datetime.now().isoformat()
            )
            # Save user to database
            user.save()
        else:
            # Update last active timestamp
            user.last_active = datetime.now().isoformat()
            user.update({'lastActive': user.last_active})
        
        # Check if user is admin
        is_admin = user.is_admin()
        
        # Set session data
        session['user_id'] = uid
        # Set admin status in session
        session['is_admin'] = is_admin
        
        # Return success message and user info
        return jsonify({
            'message': 'Login successful',
            'userId': uid,
            'is_admin': is_admin
        })
    # Catch any exceptions during login
    except Exception as e:
        # Print error to console
        print(f"Login error: {str(e)}")
        # Return error message
        return jsonify({'error': str(e)}), 401

# Define route for user logout
@auth_bp.route('/logout', methods=['POST'])
# Define the function that handles logout requests
def logout():
    """Logout and clear session"""
    # Clear all session data
    session.clear()
    # Return success message
    return jsonify({'message': 'Logged out successfully'})

# Define route for uploading profile picture
@auth_bp.route('/profile-picture', methods=['POST'])
# Define the function that handles profile picture uploads
def upload_profile_picture():
    """Upload a profile picture"""
    # Check if user is authenticated
    auth_success, user_id, error_response = check_auth()
    # If not authenticated, return error
    if not auth_success:
        return jsonify(error_response), error_response[1]
    
    try:
        # Check if file was included in request
        if 'profileImage' not in request.files:
            # Return error if no file provided
            return jsonify({'error': 'No file part'}), 400
            
        # Get file from request
        file = request.files['profileImage']
        
        # Check if file has a name
        if file.filename == '':
            # Return error if no file selected
            return jsonify({'error': 'No selected file'}), 400
            
        # Create a secure filename with user ID and UUID
        filename = f"{user_id}_{uuid.uuid4()}_{secure_filename(file.filename)}"
        
        # Variable to store temporary file path
        temp_path = None
        try:
            # Save file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                # Get temporary file path
                temp_path = temp.name
                # Save uploaded file to temporary location
                file.save(temp_path)
                
            # Create reference to file in Firebase Storage
            blob = bucket.blob(f"profile_photos/{filename}")
            # Upload file from temporary location to Firebase
            blob.upload_from_filename(temp_path)
            # Make the file publicly accessible
            blob.make_public()
            # Get public URL for the file
            public_url = blob.public_url
            
            # Get reference to user document in Firestore
            user_ref = db.collection('users').document(user_id)
            
            # Check if user already has a profile picture
            user_doc = user_ref.get()
            # If user document exists
            if user_doc.exists:
                # Convert document to dictionary
                user_data = user_doc.to_dict()
                # If user has a profile picture
                if user_data.get('profilePicture'):
                    try:
                        # Get URL of old profile picture
                        old_image_url = user_data['profilePicture']
                        # Extract filename from URL
                        old_filename = old_image_url.split('/profile_photos/')[1] if '/profile_photos/' in old_image_url else None
                        # If filename was found
                        if old_filename:
                            # Get reference to old file in Firebase Storage
                            old_blob = bucket.blob(f"profile_photos/{old_filename}")
                            # Delete old file
                            old_blob.delete()
                    # Catch errors during deletion
                    except Exception as e:
                        # Print error message
                        print(f"Error deleting old profile picture: {e}")
            
            # Update user document with new profile picture URL
            user_ref.update({
                'profilePicture': public_url,
                'lastActive': datetime.now().isoformat()
            })
            
            # Return success with new image URL
            return jsonify({'imageUrl': public_url}), 200
        # Always execute this block
        finally:
            # Delete temporary file if it exists
            if temp_path and os.path.exists(temp_path):
                try:
                    # Remove temporary file
                    os.unlink(temp_path)
                # Catch errors during file deletion
                except Exception as e:
                    # Print error message
                    print(f"Error deleting temp file: {e}")
    # Catch any exceptions during upload
    except Exception as e:
        # Return error message
        return jsonify({'error': str(e)}), 500

# Define route for changing password
@auth_bp.route('/change-password', methods=['POST'])
# Define the function that handles password change requests
def change_password():
    """Change user password"""
    # Check if user is authenticated
    auth_success, user_id, error_response = check_auth()
    # If not authenticated, return error
    if not auth_success:
        return jsonify(error_response), error_response[1]
    
    try:
        data = request.json
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new password required'}), 400
        
        # Get user email from Firestore
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        email = user_data.get('email')
        
        # Update password in Firebase Auth
        # In a real app, you would verify the current password first
        auth.update_user(user_id, password=new_password)
        
        # Update last active timestamp
        db.collection('users').document(user_id).update({
            'lastActive': datetime.now().isoformat()
        })
        
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/delete-account', methods=['POST'])
def delete_account():
    """Delete user account"""
    auth_success, user_id, error_response = check_auth()
    if not auth_success:
        return jsonify(error_response), error_response[1]
    
    try:
        data = request.json
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password required for account deletion'}), 400
        
        # Get user document
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Delete profile picture if exists
        if user_data.get('profilePicture'):
            try:
                image_url = user_data['profilePicture']
                filename = image_url.split('/profile_photos/')[1] if '/profile_photos/' in image_url else None
                if filename:
                    blob = bucket.blob(f"profile_photos/{filename}")
                    blob.delete()
            except Exception as e:
                print(f"Error deleting profile picture: {e}")
        
        # Delete user's tasks
        tasks = db.collection('tasks').where('userId', '==', user_id).stream()
        for task in tasks:
            task_data = task.to_dict()
            
            # Delete task image if exists
            if task_data.get('imageUrl'):
                try:
                    image_url = task_data['imageUrl']
                    if '/image_photo/' in image_url:
                        filename = image_url.split('/image_photo/')[1]
                        blob = bucket.blob(f"image_photo/{filename}")
                        blob.delete()
                except Exception as e:
                    print(f"Error deleting task image: {e}")
            
            # Delete task document
            task.reference.delete()
        
        # Delete user document
        db.collection('users').document(user_id).delete()
        
        # Delete user from Firebase Auth
        auth.delete_user(user_id)
        
        # Clear session
        session.clear()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users - admin only"""
    auth_success, user_id, error_response = check_admin()
    if not auth_success:
        return jsonify(error_response), error_response['code']
    
    try:
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        
        users = []
        for doc in users_docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            users.append(user_data)
        
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user - admin only"""
    auth_success, admin_id, error_response = check_admin()
    if not auth_success:
        return jsonify(error_response), error_response['code']
    
    try:
        data = request.json
        is_admin = data.get('is_admin')
        
        if is_admin is None:
            return jsonify({'error': 'is_admin field is required'}), 400
        
        # Update user admin status
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_ref.update({
            'is_admin': bool(is_admin),
            'updatedAt': datetime.now().isoformat()
        })
        
        # Get updated user data
        updated_user = user_ref.get().to_dict()
        updated_user['id'] = user_id
        
        return jsonify(updated_user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user - admin only"""
    auth_success, admin_id, error_response = check_admin()
    if not auth_success:
        return jsonify(error_response), error_response['code']
    
    try:
        # Don't allow admin to delete themselves
        if user_id == admin_id:
            return jsonify({'error': 'Cannot delete your own account through admin interface'}), 400
        
        # Get user document
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Delete profile picture if exists
        if user_data.get('profilePicture'):
            try:
                image_url = user_data['profilePicture']
                filename = image_url.split('/profile_photos/')[1] if '/profile_photos/' in image_url else None
                if filename:
                    blob = bucket.blob(f"profile_photos/{filename}")
                    blob.delete()
            except Exception as e:
                print(f"Error deleting profile picture: {e}")
        
        # Delete user's tasks
        tasks = db.collection('tasks').where('userId', '==', user_id).stream()
        for task in tasks:
            task_data = task.to_dict()
            
            # Delete task image if exists
            if task_data.get('imageUrl'):
                try:
                    image_url = task_data['imageUrl']
                    if '/image_photo/' in image_url:
                        filename = image_url.split('/image_photo/')[1]
                        blob = bucket.blob(f"image_photo/{filename}")
                        blob.delete()
                except Exception as e:
                    print(f"Error deleting task image: {e}")
            
            # Delete task document
            task.reference.delete()
        
        # Delete user document
        user_ref.delete()
        
        # Delete user from Firebase Auth
        auth.delete_user(user_id)
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<user_id>/role', methods=['PUT'])
# Define the function that handles updating user role
def update_user_role(user_id):
    """Update user role (admin status)"""
    
    # Check if the current user is an admin
    admin_success, admin_id, error_response = check_admin()
    # If not admin, return error
    if not admin_success:
        return jsonify(error_response), error_response.get('code', 403)
        
    try:
        # Get request data
        data = request.json
        # Get admin status from request
        is_admin = data.get('is_admin')
        
        # Check if is_admin field was provided
        if is_admin is None:
            return jsonify({'error': 'is_admin field is required'}), 400
            
        # Get user
        user = User.get_by_id(user_id)
        # If user not found, return error
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user is already an admin
        admin = Admin.get_by_user_id(user_id)
        
        # If should be admin but not currently an admin
        if is_admin and not admin:
            # Create admin record from user
            Admin.create_for_user(user_id, granted_by=admin_id)
        # If should not be admin but is currently an admin
        elif not is_admin and admin:
            # Deactivate admin record
            admin.deactivate()
            
        # Return success message
        return jsonify({'message': 'User role updated successfully'})
    except Exception as e:
        # Return error message
        return jsonify({'error': str(e)}), 400 