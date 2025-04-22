"""
Migration script to convert existing users with is_admin flag to use the new Admin model.
Run this script after implementing the Admin model to maintain existing admin users.
"""

from firebase_admin import firestore, credentials, initialize_app
import os
import sys
from datetime import datetime

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the models
from app.models import User, Admin

def migrate_admins():
    """
    Find all users with is_admin=True and create Admin records for them
    """
    print("Starting admin migration...")
    
    # Get Firestore database client
    db = firestore.client()
    
    # Query all users with is_admin=True
    query = db.collection('users').where('is_admin', '==', True)
    docs = query.get()
    
    # Counter for migrated admins
    migrated_count = 0
    
    # Iterate through admin users
    for doc in docs:
        user_id = doc.id
        user_data = doc.to_dict()
        
        print(f"Processing user: {user_id} ({user_data.get('email')})")
        
        # Get the user model
        user = User.get_by_id(user_id)
        
        if not user:
            print(f"  User {user_id} not found in database, skipping")
            continue
            
        # Check if an Admin record already exists for this user
        admin = Admin.get_by_user_id(user_id)
        
        if not admin:
            # Create new Admin record from this user
            admin = Admin.create_for_user(user_id)
            
            if admin:
                migrated_count += 1
                print(f"  Created admin record for user {user_id}")
            else:
                print(f"  Failed to create admin record for user {user_id}")
        else:
            print(f"  Admin record already exists for user {user_id}")
            
    print(f"Migration complete. {migrated_count} admin records created.")
    
    # Optional: Remove is_admin field from users
    # Uncomment the following code to remove the field after confirming migration is successful
    """
    print("\nRemoving is_admin field from users...")
    for doc in docs:
        user_id = doc.id
        db.collection('users').document(user_id).update({
            'is_admin': firestore.DELETE_FIELD
        })
        print(f"Removed is_admin field from user {user_id}")
    """

if __name__ == "__main__":
    # Initialize Firebase if not already initialized
    try:
        db = firestore.client()
    except:
        # Load Firebase credentials from the JSON file
        cred = credentials.Certificate('firebase-key.json')
        # Initialize Firebase app
        initialize_app(cred)
    
    # Run migration
    migrate_admins() 