from firebase_admin import firestore, storage
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
import tempfile
from .category_model import Category

class Task(Category):
    """
    Task model class that inherits from Category.
    This represents a task which is a specialized form of a category.
    """
    
    def __init__(self, task_id=None, title=None, description=None, status=None, 
                 user_id=None, due_date=None, image_url=None, created_at=None, 
                 updated_at=None, category_id=None, name=None, color=None, 
                 category_created_at=None):
        """
        Initialize a new Task instance
        
        :param task_id: Unique identifier for the task
        :param title: Task title
        :param description: Task description
        :param status: Task status (pending, in-progress, completed)
        :param user_id: ID of the user who owns the task
        :param due_date: Due date for the task
        :param image_url: URL to task's attached image
        :param created_at: Timestamp when task was created
        :param updated_at: Timestamp when task was last updated
        :param category_id: ID of the category (parent)
        :param name: Category name (from parent)
        :param color: Category color (from parent)
        :param category_created_at: Category creation timestamp (from parent)
        """
        # Initialize parent Category class
        super().__init__(
            category_id=category_id,
            name=name,
            color=color,
            created_at=category_created_at
        )
        
        # Task-specific properties
        self.task_id = task_id
        self.title = title
        self.description = description
        self.status = status or 'pending'
        self.user_id = user_id
        self.image_url = image_url
        self.due_date = due_date
        self.created_at = created_at
        self.updated_at = updated_at or datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, task_id, data):
        """
        Create a Task instance from a Firestore document
        
        :param task_id: Task ID
        :param data: Dictionary data from Firestore
        :return: Task instance
        """
        # Get category data for this task
        category_id = data.get('categoryId')
        category_data = {}
        if category_id:
            category = Category.get_by_id(category_id)
            if category:
                category_data = {
                    'name': category.name,
                    'color': category.color,
                    'category_created_at': category.created_at
                }
        
        return cls(
            task_id=task_id,
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status'),
            user_id=data.get('userId'),
            due_date=data.get('dueDate'),
            image_url=data.get('imageUrl'),
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt'),
            category_id=category_id,
            **category_data
        )
    
    def to_dict(self):
        """
        Convert Task instance to a dictionary for Firestore
        
        :return: Dictionary representation of Task
        """
        task_dict = {
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'userId': self.user_id,
            'updatedAt': datetime.now().isoformat()
        }
        
        if self.category_id:
            task_dict['categoryId'] = self.category_id
            
        if self.image_url:
            task_dict['imageUrl'] = self.image_url
            
        if self.due_date:
            task_dict['dueDate'] = self.due_date
            
        if not self.created_at:
            task_dict['createdAt'] = firestore.SERVER_TIMESTAMP
            
        return task_dict
    
    @classmethod
    def get_by_id(cls, task_id):
        """
        Get a task by its ID
        
        :param task_id: Task ID
        :return: Task instance or None
        """
        db = firestore.client()
        doc_ref = db.collection('tasks').document(task_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return cls.from_dict(task_id, doc.to_dict())
        return None
    
    @classmethod
    def get_all_by_user(cls, user_id, category_id=None, status=None):
        """
        Get all tasks for a user, optionally filtered by category and status
        
        :param user_id: User ID
        :param category_id: Category ID filter (optional)
        :param status: Status filter (optional)
        :return: List of Task instances
        """
        db = firestore.client()
        query = db.collection('tasks').where('userId', '==', user_id)
        
        if category_id and category_id != 'all':
            query = query.where('categoryId', '==', category_id)
            
        if status and status != 'all':
            query = query.where('status', '==', status)
            
        docs = query.get()
        
        tasks = []
        for doc in docs:
            tasks.append(cls.from_dict(doc.id, doc.to_dict()))
        return tasks
    
    @classmethod
    def get_all(cls, admin=False):
        """
        Get all tasks (admin only)
        
        :param admin: Whether this is an admin request
        :return: List of Task instances
        """
        if not admin:
            return []
            
        db = firestore.client()
        docs = db.collection('tasks').get()
        
        tasks = []
        for doc in docs:
            tasks.append(cls.from_dict(doc.id, doc.to_dict()))
        return tasks
    
    def save(self):
        """
        Save the task to Firestore
        
        :return: Task ID
        """
        db = firestore.client()
        
        if not self.task_id:
            # Create new document
            doc_ref = db.collection('tasks').document()
            self.task_id = doc_ref.id
        else:
            # Update existing document
            doc_ref = db.collection('tasks').document(self.task_id)
            
        doc_ref.set(self.to_dict(), merge=True)
        
        # If this is a new task, increment the user's task count
        if not self.created_at:
            user_ref = db.collection('users').document(self.user_id)
            user_ref.update({
                'taskCount': firestore.Increment(1),
                'lastActive': datetime.now().isoformat()
            })
            
        return self.task_id
    
    def update(self, data):
        """
        Update task with new data
        
        :param data: Dictionary of data to update
        :return: True if successful
        """
        db = firestore.client()
        doc_ref = db.collection('tasks').document(self.task_id)
        
        # Update the model with the new data
        if 'title' in data:
            self.title = data['title']
        if 'description' in data:
            self.description = data['description']
        if 'status' in data:
            self.status = data['status']
        if 'categoryId' in data:
            self.category_id = data['categoryId']
            # Fetch new category data if available
            if self.category_id:
                category = Category.get_by_id(self.category_id)
                if category:
                    self.name = category.name
                    self.color = category.color
        if 'dueDate' in data:
            self.due_date = data['dueDate']
        
        # Add updatedAt timestamp
        data['updatedAt'] = datetime.now().isoformat()
        self.updated_at = data['updatedAt']
        
        doc_ref.update(data)
        return True
    
    def delete(self):
        """
        Delete the task from Firestore
        
        :return: True if successful
        """
        db = firestore.client()
        
        # Delete the task document
        db.collection('tasks').document(self.task_id).delete()
        
        # If task had an image, delete it from storage
        if self.image_url:
            try:
                # Extract filename from URL
                filename = self.image_url.split('/task_images/')[1]
                
                # Delete from Firebase Storage
                bucket = storage.bucket()
                blob = bucket.blob(f'task_images/{filename}')
                blob.delete()
            except Exception as e:
                print(f"Error deleting image: {str(e)}")
        
        # Decrement user's task count
        user_ref = db.collection('users').document(self.user_id)
        user_ref.update({
            'taskCount': firestore.Increment(-1),
            'lastActive': datetime.now().isoformat()
        })
        
        return True
    
    def mark_complete(self):
        """
        Mark the task as completed
        
        :return: True if successful
        """
        return self.update({'status': 'completed'})
    
    def attach_image(self, file):
        """
        Attach an image to the task
        
        :param file: Image file to attach
        :return: Public URL of the uploaded image
        """
        if not file or file.filename == '':
            return None
            
        # Create a secure filename
        filename = f"task_{self.task_id}_{uuid.uuid4()}_{secure_filename(file.filename)}"
        
        # Save to temporary file
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp_path = temp.name
                file.save(temp_path)
                
            # Upload to Firebase Storage
            bucket = storage.bucket()
            blob = bucket.blob(f"task_images/{filename}")
            blob.upload_from_filename(temp_path)
            
            # Make public
            blob.make_public()
            public_url = blob.public_url
            
            # Update task with image URL
            self.image_url = public_url
            self.update({'imageUrl': public_url})
            
            return public_url
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        
        return None
    
    @classmethod
    def get_task_counts_by_category(cls, user_id=None):
        """
        Get count of tasks in each category
        
        :param user_id: User ID to filter by (optional)
        :return: Dictionary with category IDs as keys and counts as values
        """
        db = firestore.client()
        tasks_ref = db.collection('tasks')
        
        # If user_id provided, filter by user
        if user_id:
            tasks = tasks_ref.where('userId', '==', user_id).get()
        else:
            tasks = tasks_ref.get()
            
        # Count tasks by category
        counts = {}
        for task in tasks:
            task_data = task.to_dict()
            category_id = task_data.get('categoryId')
            
            if not category_id:
                continue
                
            if category_id in counts:
                counts[category_id] += 1
            else:
                counts[category_id] = 1
                
        return counts
    
    def get_category_name(self):
        """
        Get the name of this task's category
        
        :return: Category name or 'Uncategorized'
        """
        if self.name:
            return self.name
        return 'Uncategorized'
    
    def get_category_color(self):
        """
        Get the color of this task's category
        
        :return: Category color or default color
        """
        if self.color:
            return self.color
        return '#6c757d'  # Default gray 