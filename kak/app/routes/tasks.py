# Import necessary Flask components
from flask import Blueprint, request, jsonify, session
# Import Firebase Firestore database and storage
from firebase_admin import firestore, storage
# Import UUID for generating unique identifiers
import uuid
# Import datetime for handling dates and times
from datetime import datetime
# Import tempfile for creating temporary files
import tempfile
# Import os for file operations
import os
# Import secure_filename to sanitize file names
from werkzeug.utils import secure_filename

# Create a Blueprint named 'tasks' with URL prefix '/tasks'
tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')
# Create a Firestore database client
db = firestore.client()
# Get reference to Firebase storage bucket
bucket = storage.bucket()

# Define function to check if user is authenticated
def check_auth():
    """Check if user is authenticated"""
    # Get user ID from session
    user_id = session.get('user_id')
    # If no user ID is found, return authentication error
    if not user_id:
        return False, {'error': 'Authentication required'}, 401
    # If user ID is found, return success with user ID
    return True, user_id, None

# Define route for getting all tasks
@tasks_bp.route('/', methods=['GET'])
# Define function to handle GET requests for tasks
def get_tasks():
    """Get all tasks for the current user"""
    # Check if user is authenticated
    auth_success, result, code = check_auth()
    # If not authenticated, return error
    if not auth_success:
        return jsonify(result), code
    
    # Get user ID from authentication result
    user_id = result
    
    try:
        # Get tasks from Firestore that belong to the current user
        tasks_ref = db.collection('tasks').where('userId', '==', user_id).stream()
        # Create empty list to store tasks
        tasks = []
        
        # Loop through each task from the database
        for task in tasks_ref:
            # Convert task document to dictionary
            task_data = task.to_dict()
            # Add the task ID to the data
            task_data['id'] = task.id
            # Add the task to the tasks list
            tasks.append(task_data)
            
        # Return all tasks as JSON
        return jsonify(tasks)
    # Catch any exceptions
    except Exception as e:
        # Return error message
        return jsonify({'error': str(e)}), 500

# Define route for creating a new task
@tasks_bp.route('/', methods=['POST'])
# Define function to handle POST requests for creating tasks
def create_task():
    """Create a new task"""
    # Check if user is authenticated
    auth_success, result, code = check_auth()
    # If not authenticated, return error
    if not auth_success:
        return jsonify(result), code
    
    # Get user ID from authentication result
    user_id = result
    
    try:
        # Print request details for debugging
        print("Request headers:", request.headers)
        # Print form data for debugging
        print("Request form data:", request.form)
        # Print file information for debugging
        print("Request files:", request.files)
        # Print file keys for debugging
        print("Files dict keys:", list(request.files.keys()))
        
        # Get form data as dictionary
        data = request.form.to_dict()
        # Get task title from form data
        title = data.get('title')
        # Get task description or empty string if not provided
        description = data.get('description', '')
        # Get task category or 'other' if not provided
        category = data.get('category', 'other')  # Default to 'other' if no category provided
        # Get task urgency or 'medium' if not provided
        urgency = data.get('urgency', 'medium')
        # Get task due date or None if not provided
        due_date = data.get('dueDate')
        
        # Validate that title is provided
        if not title:
            # Return error if title is missing
            return jsonify({'error': 'Title is required'}), 400
        
        # Create dictionary with task data
        task_data = {
            'title': title,
            'description': description,
            'userId': user_id,
            'status': 'pending',
            'category': category,
            'urgency': urgency,
            'dueDate': due_date,
            'createdAt': datetime.now().isoformat(),
            'imageUrl': None
        }
        
        # Check if an image file is included in the request
        if 'image' in request.files:
            # Get the image file
            image_file = request.files['image']
            # Log received file name
            print("Image file received:", image_file.filename)
            
            # Check if file has a name (not empty)
            if image_file.filename != '':
                # Create secure filename with user ID and UUID
                filename = f"{user_id}_{uuid.uuid4()}_{secure_filename(image_file.filename)}"
                # Log the created filename
                print("Secure filename created:", filename)
                
                # Variable to store temporary file path
                temp_path = None
                try:
                    # Save image to temporary file
                    with tempfile.NamedTemporaryFile(delete=False) as temp:
                        # Get the temporary file path
                        temp_path = temp.name
                        # Save the uploaded file to temporary path
                        image_file.save(temp_path)
                        # Log temp file save
                        print("Saved to temp file:", temp_path)
                    
                    # Create reference to file location in Firebase Storage
                    blob = bucket.blob(f"image_photo/{filename}")
                    # Upload image from temporary file to Firebase
                    blob.upload_from_filename(temp_path)
                    # Make the image publicly accessible
                    blob.make_public()
                    
                    # Get the public URL of the uploaded image
                    public_url = blob.public_url
                    # Log successful upload
                    print("Uploaded to Firebase, public URL:", public_url)
                    
                    # Add image URL to task data
                    task_data['imageUrl'] = public_url
                # Catch any errors during upload
                except Exception as e:
                    # Log the error
                    print(f"Error during image upload: {e}")
                    # Continue without image if there's an error
                # Always clean up temporary file
                finally:
                    # Check if temporary file exists
                    if temp_path and os.path.exists(temp_path):
                        try:
                            # Delete the temporary file
                            os.unlink(temp_path)
                            # Log successful deletion
                            print("Temporary file deleted")
                        # Catch errors during file deletion
                        except Exception as e:
                            # Log deletion error
                            print(f"Failed to delete temporary file: {e}")
                            # Continue even if we can't delete the temp file
        
        # Create a new document in the tasks collection
        task_ref = db.collection('tasks').document()
        # Save task data to Firestore
        task_ref.set(task_data)
        # Get the ID of the created task
        task_id = task_ref.id
        
        # Get reference to user document
        user_ref = db.collection('users').document(user_id)
        # Get user document
        user_doc = user_ref.get()
        
        # Check if user document exists
        if user_doc.exists:
            # Get current task count or default to 0
            current_task_count = user_doc.to_dict().get('taskCount', 0)
            # Update user document with new task count
            user_ref.update({
                'taskCount': current_task_count + 1,
                'lastTaskCreated': datetime.now().isoformat()
            })
        
        # Get reference to category document
        category_ref = db.collection('categories').document(category)
        # Get category document
        category_doc = category_ref.get()
        
        # Check if category already exists
        if category_doc.exists:
            # Get category data
            category_data = category_doc.to_dict()
            # Get list of tasks or empty list if none
            tasks_list = category_data.get('tasks', [])
            # Add new task ID to list
            tasks_list.append(task_id)
            
            # Update category document with new task
            category_ref.update({
                'tasks': tasks_list,
                'taskCount': len(tasks_list),
                'lastUpdated': datetime.now().isoformat()
            })
        else:
            # Create new category document if it doesn't exist
            category_ref.set({
                'name': category,
                'tasks': [task_id],
                'taskCount': 1,
                'createdAt': datetime.now().isoformat(),
                'lastUpdated': datetime.now().isoformat()
            })
            
        # Add task ID to the response data
        task_data['id'] = task_id
        
        # Return created task data and 201 status code
        return jsonify(task_data), 201
    # Catch any exceptions
    except Exception as e:
        # Return error message
        return jsonify({'error': str(e)}), 500

# Define route for getting a specific task by ID
@tasks_bp.route('/<task_id>', methods=['GET'])
# Define function to handle GET requests for a specific task
def get_task(task_id):
    """Get a specific task"""
    # Check if user is authenticated
    auth_success, result, code = check_auth()
    # If not authenticated, return error
    if not auth_success:
        return jsonify(result), code
    
    # Get user ID from authentication result
    user_id = result
    
    try:
        # Get task document from Firestore by ID
        task_ref = db.collection('tasks').document(task_id).get()
        
        # Check if task exists
        if not task_ref.exists:
            # Return error if task not found
            return jsonify({'error': 'Task not found'}), 404
            
        # Convert task document to dictionary
        task_data = task_ref.to_dict()
        
        # Check if user has permission to access this task
        if task_data['userId'] != user_id and not session.get('is_admin'):
            # Return error if unauthorized
            return jsonify({'error': 'Unauthorized access'}), 403
            
        # Add task ID to data
        task_data['id'] = task_ref.id
        # Return task data as JSON
        return jsonify(task_data)
    # Catch any exceptions
    except Exception as e:
        # Return error message
        return jsonify({'error': str(e)}), 500

# Define route for updating a task
@tasks_bp.route('/<task_id>', methods=['PUT'])
# Define function to handle PUT requests for updating tasks
def update_task(task_id):
    """Update a task"""
    auth_success, result, code = check_auth()
    if not auth_success:
        return jsonify(result), code
    
    user_id = result
    
    try:
        # Get the current task
        task_ref = db.collection('tasks').document(task_id)
        task = task_ref.get()
        
        if not task.exists:
            return jsonify({'error': 'Task not found'}), 404
            
        task_data = task.to_dict()
        old_category = task_data.get('category', 'other')
        
        # Check if the task belongs to the user
        if task_data['userId'] != user_id and not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Update task fields from form data
        data = request.form.to_dict()
        
        # Update relevant fields
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'status' in data:
            update_data['status'] = data['status']
        
        # Handle category update
        new_category = data.get('category', old_category)
        update_data['category'] = new_category
        
        # Handle urgency update
        if 'urgency' in data:
            update_data['urgency'] = data['urgency']
        
        # Handle due date update
        if 'dueDate' in data:
            update_data['dueDate'] = data['dueDate']
        
        # Handle image upload if present
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                # Delete old image if exists
                if task_data.get('imageUrl'):
                    try:
                        # Extract the file name from the URL path
                        image_url = task_data['imageUrl']
                        # URL format: https://storage.googleapis.com/roeeki-a4ca2.firebasestorage.app/image_photo/filename
                        file_path = image_url.split('/o/')[1].split('?')[0] if '/o/' in image_url else image_url.split('/image_photo/')[1]
                        file_path = file_path.replace('%2F', '/') # Fix URL encoding if present
                        
                        print(f"Attempting to delete image: {file_path}")
                        blob = bucket.blob(f"image_photo/{file_path}")
                        blob.delete()
                        print(f"Deleted image from storage: {file_path}")
                    except Exception as e:
                        print(f"Error deleting image from storage: {e}")
                        # Continue with task deletion even if image deletion fails
                
                # Create a secure filename
                filename = f"{user_id}_{uuid.uuid4()}_{secure_filename(image_file.filename)}"
                
                # Create a temporary file for the upload
                temp_path = None
                try:
                    # Save to a temporary file using a context manager to ensure it's closed
                    with tempfile.NamedTemporaryFile(delete=False) as temp:
                        temp_path = temp.name
                        image_file.save(temp_path)
                        print("Saved to temp file:", temp_path)
                    
                    # Upload to Firebase Storage - after the file is properly closed
                    blob = bucket.blob(f"image_photo/{filename}")
                    blob.upload_from_filename(temp_path)
                    blob.make_public()
                    
                    # Get and print the public URL
                    public_url = blob.public_url
                    print("Uploaded to Firebase, public URL:", public_url)
                    
                    # Update task data with image URL
                    update_data['imageUrl'] = public_url
                except Exception as e:
                    print(f"Error during image upload: {e}")
                    # Continue without image if there's an error
                finally:
                    # Clean up temporary file
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                            print("Temporary file deleted")
                        except Exception as e:
                            print(f"Failed to delete temporary file: {e}")
                            # Continue even if we can't delete the temp file
        
        # Update task in Firestore
        task_ref.update(update_data)
        
        # Handle category change if needed
        if new_category != old_category:
            # Remove task from old category
            old_category_ref = db.collection('categories').document(old_category)
            old_category_doc = old_category_ref.get()
            
            if old_category_doc.exists:
                old_category_data = old_category_doc.to_dict()
                old_tasks_list = old_category_data.get('tasks', [])
                
                if task_id in old_tasks_list:
                    old_tasks_list.remove(task_id)
                    
                    # Update old category
                    old_category_ref.update({
                        'tasks': old_tasks_list,
                        'taskCount': len(old_tasks_list),
                        'lastUpdated': datetime.now().isoformat()
                    })
            
            # Add task to new category
            new_category_ref = db.collection('categories').document(new_category)
            new_category_doc = new_category_ref.get()
            
            if new_category_doc.exists:
                # Category exists, add task to tasks array
                new_category_data = new_category_doc.to_dict()
                new_tasks_list = new_category_data.get('tasks', [])
                
                if task_id not in new_tasks_list:
                    new_tasks_list.append(task_id)
                    
                    # Update category with new task
                    new_category_ref.update({
                        'tasks': new_tasks_list,
                        'taskCount': len(new_tasks_list),
                        'lastUpdated': datetime.now().isoformat()
                    })
            else:
                # Create new category document
                new_category_ref.set({
                    'name': new_category,
                    'tasks': [task_id],
                    'taskCount': 1,
                    'createdAt': datetime.now().isoformat(),
                    'lastUpdated': datetime.now().isoformat()
                })
        
        # Get updated task
        updated_task = task_ref.get().to_dict()
        updated_task['id'] = task_id
        
        return jsonify(updated_task)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    auth_success, result, code = check_auth()
    if not auth_success:
        return jsonify(result), code
    
    user_id = result
    
    try:
        # Get the task
        task_ref = db.collection('tasks').document(task_id)
        task = task_ref.get()
        
        if not task.exists:
            return jsonify({'error': 'Task not found'}), 404
            
        task_data = task.to_dict()
        task_category = task_data.get('category', 'other')
        
        # Check if the task belongs to the user
        if task_data['userId'] != user_id and not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Delete the image if exists
        if task_data.get('imageUrl'):
            try:
                # Extract the file name from the URL path
                image_url = task_data['imageUrl']
                # URL format: https://storage.googleapis.com/roeeki-a4ca2.firebasestorage.app/image_photo/filename
                file_path = image_url.split('/o/')[1].split('?')[0] if '/o/' in image_url else image_url.split('/image_photo/')[1]
                file_path = file_path.replace('%2F', '/') # Fix URL encoding if present
                
                print(f"Attempting to delete image: {file_path}")
                blob = bucket.blob(f"image_photo/{file_path}")
                blob.delete()
                print(f"Deleted image from storage: {file_path}")
            except Exception as e:
                print(f"Error deleting image from storage: {e}")
                # Continue with task deletion even if image deletion fails
        
        # Delete the task
        task_ref.delete()
        
        # Update user's task count in the users collection
        task_owner_id = task_data['userId']
        user_ref = db.collection('users').document(task_owner_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            # Get current task count or default to 0
            current_task_count = user_doc.to_dict().get('taskCount', 0)
            # Update with decremented count (ensure it doesn't go below 0)
            user_ref.update({
                'taskCount': max(0, current_task_count - 1),
                'lastTaskDeleted': datetime.now().isoformat()
            })
        
        # Remove task from category
        category_ref = db.collection('categories').document(task_category)
        category_doc = category_ref.get()
        
        if category_doc.exists:
            category_data = category_doc.to_dict()
            tasks_list = category_data.get('tasks', [])
            
            if task_id in tasks_list:
                tasks_list.remove(task_id)
                
                # Update category with removed task
                if tasks_list:
                    category_ref.update({
                        'tasks': tasks_list,
                        'taskCount': len(tasks_list),
                        'lastUpdated': datetime.now().isoformat()
                    })
                else:
                    # If no tasks left, delete the category
                    category_ref.delete()
        
        return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with their task counts"""
    auth_success, result, code = check_auth()
    if not auth_success:
        return jsonify(result), code
    
    try:
        # Get all categories from Firestore
        categories_ref = db.collection('categories').stream()
        categories = []
        
        for category in categories_ref:
            category_data = category.to_dict()
            categories.append({
                'id': category.id,
                'name': category_data.get('name', category.id),
                'taskCount': category_data.get('taskCount', 0),
                'lastUpdated': category_data.get('lastUpdated')
            })
        
        # Sort categories by task count (descending)
        categories.sort(key=lambda x: x['taskCount'], reverse=True)
        
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/admin/all', methods=['GET'])
def get_all_tasks():
    """Get all tasks (admin only)"""
    # Check if user is admin
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
        
    if not is_admin:
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        # Get all tasks
        tasks_ref = db.collection('tasks')
        tasks_docs = tasks_ref.stream()
        
        # Get all users to map user IDs to emails
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        
        # Create a dictionary to map user IDs to emails
        user_emails = {}
        for doc in users_docs:
            user_data = doc.to_dict()
            user_emails[doc.id] = user_data.get('email', 'Unknown')
        
        # Process tasks
        tasks = []
        for doc in tasks_docs:
            task_data = doc.to_dict()
            task_data['id'] = doc.id
            
            # Add user email to task data
            task_data['userEmail'] = user_emails.get(task_data.get('userId'), 'Unknown')
            
            tasks.append(task_data)
            
        return jsonify(tasks), 200
    except Exception as e:
        print(f"Error getting all tasks: {e}")
        return jsonify({'error': str(e)}), 500 