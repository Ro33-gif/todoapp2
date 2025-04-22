from firebase_admin import firestore
from datetime import datetime
from .user_model import User

class Admin(User):
    """
    Admin model class that inherits from User, extending it with administrative capabilities.
    This represents a user with admin privileges.
    """
    
    def __init__(self, uid=None, email=None, profile_picture=None, task_count=0, 
                 last_active=None, created_at=None, admin_id=None, active=True, 
                 granted_at=None, granted_by=None):
        """
        Initialize a new Admin instance
        
        :param uid: Unique identifier for the user
        :param email: User's email address
        :param profile_picture: URL to user's profile picture
        :param task_count: Count of tasks created by the user
        :param last_active: Timestamp of user's last activity
        :param created_at: Timestamp when user was created
        :param admin_id: Unique identifier for the admin record
        :param active: Whether the admin privileges are active
        :param granted_at: When admin privileges were granted
        :param granted_by: User ID of who granted the privileges
        """
        # Initialize parent User class
        super().__init__(uid, email, profile_picture, task_count, last_active, created_at)
        
        # Admin-specific properties
        self.admin_id = admin_id
        self.active = active
        self.granted_at = granted_at or datetime.now().isoformat()
        self.granted_by = granted_by
    
    @classmethod
    def from_user(cls, user, admin_id=None, active=True, granted_at=None, granted_by=None):
        """
        Create an Admin instance from an existing User
        
        :param user: User instance
        :param admin_id: Admin record ID
        :param active: Whether admin privileges are active
        :param granted_at: When admin privileges were granted
        :param granted_by: User ID of who granted the privileges
        :return: Admin instance
        """
        return cls(
            uid=user.uid,
            email=user.email,
            profile_picture=user.profile_picture,
            task_count=user.task_count,
            last_active=user.last_active,
            created_at=user.created_at,
            admin_id=admin_id,
            active=active,
            granted_at=granted_at,
            granted_by=granted_by
        )
    
    def admin_to_dict(self):
        """
        Convert Admin-specific attributes to a dictionary for Firestore
        
        :return: Dictionary representation of Admin attributes
        """
        admin_dict = {
            'userId': self.uid,
            'active': self.active,
            'grantedAt': self.granted_at
        }
        
        if self.granted_by:
            admin_dict['grantedBy'] = self.granted_by
            
        return admin_dict
    
    def save(self):
        """
        Save both the user and admin data to Firestore
        
        :return: True if successful
        """
        # Save user data
        super().save()
        
        # Save admin data
        db = firestore.client()
        
        # If no admin_id, create a new document
        if not self.admin_id:
            doc_ref = db.collection('admins').document()
            self.admin_id = doc_ref.id
        else:
            doc_ref = db.collection('admins').document(self.admin_id)
            
        doc_ref.set(self.admin_to_dict())
        return True
    
    def update_admin(self, data):
        """
        Update admin record with new data
        
        :param data: Dictionary of data to update
        :return: True if successful
        """
        db = firestore.client()
        doc_ref = db.collection('admins').document(self.admin_id)
        doc_ref.update(data)
        return True
    
    def deactivate(self):
        """
        Deactivate admin privileges
        
        :return: True if successful
        """
        self.active = False
        return self.update_admin({'active': False})
    
    @classmethod
    def get_by_admin_id(cls, admin_id):
        """
        Get an admin by their admin ID
        
        :param admin_id: Admin ID
        :return: Admin instance or None
        """
        db = firestore.client()
        admin_ref = db.collection('admins').document(admin_id)
        admin_doc = admin_ref.get()
        
        if not admin_doc.exists:
            return None
            
        admin_data = admin_doc.to_dict()
        user_id = admin_data.get('userId')
        
        if not user_id:
            return None
            
        # Get user data
        user = User.get_by_id(user_id)
        
        if not user:
            return None
            
        # Create Admin from User
        return cls.from_user(
            user,
            admin_id=admin_id,
            active=admin_data.get('active', True),
            granted_at=admin_data.get('grantedAt'),
            granted_by=admin_data.get('grantedBy')
        )
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Get an admin by user ID
        
        :param user_id: User ID
        :return: Admin instance or None
        """
        db = firestore.client()
        query = db.collection('admins').where('userId', '==', user_id).where('active', '==', True).limit(1)
        docs = query.get()
        
        for doc in docs:
            return cls.get_by_admin_id(doc.id)
        return None
    
    @classmethod
    def create_for_user(cls, user_id, granted_by=None):
        """
        Create admin privileges for an existing user
        
        :param user_id: User ID to grant admin privileges to
        :param granted_by: User ID who granted the privileges
        :return: Admin instance or None
        """
        user = User.get_by_id(user_id)
        
        if not user:
            return None
            
        admin = cls.from_user(
            user,
            active=True,
            granted_at=datetime.now().isoformat(),
            granted_by=granted_by
        )
        
        admin.save()
        return admin
    
    @classmethod
    def get_all_admins(cls):
        """
        Get all active admin records
        
        :return: List of Admin instances
        """
        db = firestore.client()
        query = db.collection('admins').where('active', '==', True)
        docs = query.get()
        
        admins = []
        for doc in docs:
            admin = cls.get_by_admin_id(doc.id)
            if admin:
                admins.append(admin)
        return admins
    
    def is_admin(self):
        """
        Override the is_admin method from User
        
        :return: True if admin is active, False otherwise
        """
        return self.active 