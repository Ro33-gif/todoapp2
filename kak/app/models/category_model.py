from firebase_admin import firestore
from datetime import datetime

class Category:
    """
    Category model class representing a task category in the system.
    This class provides methods for category operations and mapping to/from Firestore.
    """
    
    def __init__(self, category_id=None, name=None, color=None, created_at=None):
        """
        Initialize a new Category instance
        
        :param category_id: Unique identifier for the category
        :param name: Category name
        :param color: Category color (hex code)
        :param created_at: Timestamp when category was created
        """
        self.category_id = category_id
        self.name = name
        self.color = color or '#17a2b8'  # Default to info blue
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, category_id, data):
        """
        Create a Category instance from a Firestore document
        
        :param category_id: Category ID
        :param data: Dictionary data from Firestore
        :return: Category instance
        """
        return cls(
            category_id=category_id,
            name=data.get('name'),
            color=data.get('color'),
            created_at=data.get('createdAt')
        )
    
    def to_dict(self):
        """
        Convert Category instance to a dictionary for Firestore
        
        :return: Dictionary representation of Category
        """
        category_dict = {
            'name': self.name,
            'color': self.color
        }
        
        if not self.created_at:
            category_dict['createdAt'] = firestore.SERVER_TIMESTAMP
            
        return category_dict
    
    @classmethod
    def get_by_id(cls, category_id):
        """
        Get a category by its ID
        
        :param category_id: Category ID
        :return: Category instance or None
        """
        db = firestore.client()
        doc_ref = db.collection('categories').document(category_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return cls.from_dict(category_id, doc.to_dict())
        return None
    
    @classmethod
    def get_all(cls):
        """
        Get all categories
        
        :return: List of Category instances
        """
        db = firestore.client()
        docs = db.collection('categories').get()
        
        categories = []
        for doc in docs:
            categories.append(cls.from_dict(doc.id, doc.to_dict()))
        return categories
    
    def save(self):
        """
        Save the category to Firestore
        
        :return: Category ID
        """
        db = firestore.client()
        
        if not self.category_id:
            # Create new document
            doc_ref = db.collection('categories').document()
            self.category_id = doc_ref.id
        else:
            # Update existing document
            doc_ref = db.collection('categories').document(self.category_id)
            
        doc_ref.set(self.to_dict(), merge=True)
        return self.category_id
    
    def update(self, data):
        """
        Update category with new data
        
        :param data: Dictionary of data to update
        :return: True if successful
        """
        db = firestore.client()
        doc_ref = db.collection('categories').document(self.category_id)
        
        # Update the model with the new data
        if 'name' in data:
            self.name = data['name']
        if 'color' in data:
            self.color = data['color']
        
        doc_ref.update(data)
        return True
    
    def delete(self):
        """
        Delete the category from Firestore
        Caution: This does not update tasks using this category
        
        :return: True if successful
        """
        db = firestore.client()
        db.collection('categories').document(self.category_id).delete()
        return True
    
    def get_tasks(self):
        """
        Get all tasks in this category
        
        :return: List of task dictionaries
        """
        db = firestore.client()
        query = db.collection('tasks').where('categoryId', '==', self.category_id)
        docs = query.get()
        
        tasks = []
        for doc in docs:
            task_data = doc.to_dict()
            task_data['id'] = doc.id
            tasks.append(task_data)
        return tasks
    
    @classmethod
    def get_default_categories(cls):
        """
        Get default categories. If none exist, create them.
        
        :return: List of Category instances
        """
        db = firestore.client()
        categories_ref = db.collection('categories')
        docs = categories_ref.get()
        
        # If categories exist, return them
        if len(list(docs)) > 0:
            return cls.get_all()
        
        # Otherwise create default categories
        default_categories = [
            {'name': 'Work', 'color': '#dc3545'},  # Red
            {'name': 'Personal', 'color': '#28a745'},  # Green
            {'name': 'Study', 'color': '#17a2b8'},  # Blue
            {'name': 'Health', 'color': '#6610f2'},  # Purple
            {'name': 'Shopping', 'color': '#fd7e14'},  # Orange
        ]
        
        created_categories = []
        for cat_data in default_categories:
            category = cls(name=cat_data['name'], color=cat_data['color'])
            category.save()
            created_categories.append(category)
            
        return created_categories 