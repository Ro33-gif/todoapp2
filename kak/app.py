# Import the create_app function from the app package
from app import create_app
# Import the os module for environment variable access
import os
# Import load_dotenv to load environment variables from .env file
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a Flask application using the create_app function
app = create_app()

# Check if this file is being run directly (not imported)
if __name__ == '__main__':
    # Run the Flask application in debug mode
    app.run(debug=True) 