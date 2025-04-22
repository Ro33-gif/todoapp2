# Import necessary components from Flask
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
# Import requests library for making HTTP requests
import requests
# Import Firestore database from Firebase
from firebase_admin import firestore

# Create a Blueprint named 'main' for organizing routes
main_bp = Blueprint('main', __name__)
# Create a Firestore database client
db = firestore.client()

# Define route for the homepage
@main_bp.route('/')
# Define the function that handles the homepage request
def index():
    """Main dashboard page"""
    # Render the index.html template and return it
    return render_template('index.html')

# Define route for the profile page
@main_bp.route('/profile')
# Define the function that handles the profile page request
def profile():
    """User profile page"""
    # Check if user is logged in by looking for user_id in session
    if 'user_id' not in session:
        # If not logged in, redirect to the homepage
        return redirect(url_for('main.index'))
    
    # If logged in, render the profile page
    return render_template('profile.html')

# Define route for the admin panel
@main_bp.route('/admin')
# Define the function that handles the admin panel request
def admin():
    """Admin panel page"""
    # Get the user ID from the session
    user_id = session.get('user_id')
    # If no user ID (not logged in), redirect to homepage
    if not user_id:
        return redirect(url_for('main.index'))
    
    # Check if the user is marked as admin in the session
    is_admin = session.get('is_admin')
    # If not marked as admin in session, verify from database
    if not is_admin:
        # Get reference to the user document in Firestore
        user_ref = db.collection('users').document(user_id)
        # Get the user document
        user_doc = user_ref.get()
        
        # Check if the user document exists
        if user_doc.exists:
            # Convert document to dictionary
            user_data = user_doc.to_dict()
            # Check if the user has admin privileges in the database
            if user_data.get('is_admin') == True:
                # Update session with admin status
                session['is_admin'] = True
                # Render admin panel
                return render_template('admin.html')
    
        # If user is not admin, redirect to homepage
        return redirect(url_for('main.index'))
    
    # If user is admin, render admin panel
    return render_template('admin.html')

# Define route for getting random inspirational quotes
@main_bp.route('/quote')
# Define the function that handles the quote request
def get_quote():
    """Get a random quote from API Ninjas"""
    try:
        # Set the API URL for quotes
        api_url = 'https://api.api-ninjas.com/v1/quotes'
        # Set headers with API key for authentication
        headers = {
            'X-Api-Key': 'whXhcw6atow6MmzGEuJTgQ==34nA35P7ioKTsheO'
        }
        
        # Make GET request to the API
        response = requests.get(api_url, headers=headers)
        
        # Check if the API response was successful
        if not response.ok:
            # Return error if API request failed
            return jsonify({'error': f'API error: {response.status_code}'}), 500
            
        # Convert API response to JSON
        data = response.json()
        
        # Validate the API response format
        if not data or not isinstance(data, list) or len(data) == 0:
            # Return error if response format is invalid
            return jsonify({'error': 'Invalid API response format'}), 500
            
        # Get the first quote from the response array
        quote_data = data[0]
        
        # Prepare and return quote data as JSON
        return jsonify({
            'content': quote_data.get('quote', 'No content available'),
            'author': quote_data.get('author', 'Unknown'),
            'category': quote_data.get('category', 'General')
        })
    # Handle network/connection errors
    except requests.RequestException as e:
        return jsonify({'error': f'Request error: {str(e)}'}), 500
    # Handle JSON parsing errors
    except ValueError as e:  # JSON parsing error
        return jsonify({'error': f'JSON parsing error: {str(e)}'}), 500
    # Handle any other unexpected errors
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500 