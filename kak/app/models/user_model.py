from firebase_admin import firestore
from datetime import datetime

class User:
    """
    User model class representing a user in the system.
    This class provides methods for user operations and mapping to/from Firestore.
    """
    
    def __init__(self, uid=None, email=None, profile_picture=None, task_count=0, 
                 last_active=None, created_at=None):
        """
        Initialize a new User instance
        
        :param uid: Unique identifier for the user
        :param email: User's email address
        :param profile_picture: URL to user's profile picture
        :param task_count: Count of tasks created by the user
        :param last_active: Timestamp of user's last activity
        :param created_at: Timestamp when user was created
        """
        self.uid = uid
        self.email = email
        self.profile_picture = profile_picture
        self.task_count = task_count
        self.last_active = last_active or datetime.now().isoformat()
        self.created_at = created_at
        
    @classmethod
    def from_dict(cls, uid, data):
        """
        Create a User instance from a Firestore document
        
        :param uid: User ID
        :param data: Dictionary data from Firestore
        :return: User instance
        """
        return cls(
            uid=uid,
            email=data.get('email'),
            profile_picture=data.get('profilePicture'),
            task_count=data.get('taskCount', 0),
            last_active=data.get('lastActive'),
            created_at=data.get('created_at')
        )
    
    def to_dict(self):
        """
        Convert User instance to a dictionary for Firestore
        
        :return: Dictionary representation of User
        """
        user_dict = {
            'email': self.email,
            'taskCount': self.task_count,
            'lastActive': self.last_active,
        }
        
        if self.profile_picture:
            user_dict['profilePicture'] = self.profile_picture
            
        if not self.created_at:
            user_dict['created_at'] = firestore.SERVER_TIMESTAMP
            
        return user_dict
    
    @classmethod
    def get_by_id(cls, uid):
        """
        Get a user by their UID
        
        :param uid: User ID
        :return: User instance or None
        """
        db = firestore.client()
        doc_ref = db.collection('users').document(uid)
        doc = doc_ref.get()
        
        if doc.exists:
            return cls.from_dict(uid, doc.to_dict())
        return None
    
    def save(self):
        """
        Save the user to Firestore
        
        :return: True if successful
        """
        db = firestore.client()
        doc_ref = db.collection('users').document(self.uid)
        doc_ref.set(self.to_dict(), merge=True)
        return True
    
    def update(self, data):
        """
        Update user with new data
        
        :param data: Dictionary of data to update
        :return: True if successful
        """
        db = firestore.client()
        doc_ref = db.collection('users').document(self.uid)
        doc_ref.update(data)
        return True
        
    def is_admin(self):
        """
        Check if the user has admin privileges by checking for an Admin record
        
        :return: True if user is an admin
        """
        from .admin_model import Admin
        admin = Admin.get_by_user_id(self.uid)
        return admin is not None 