# Todo App

A Flask-based todo application with Firebase integration for authentication and data storage.

## Features
- User authentication (signup/login)
- Task management (create, read, update, delete)
- Admin panel
- Firebase integration
- Responsive design

## Setup Instructions

1. Install Python (3.8 or newer)
2. Clone this repository
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
6. Create a `.env` file based on `.env.example`
7. Add your Firebase credentials (firebase-key.json)
8. Run the application:
   ```
   python app.py
   ```

## Environment Variables
Create a `.env` file with the following variables:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
FIREBASE_STORAGE_BUCKET=your_firebase_bucket
```

## Security Note
Never commit your `.env` file or `firebase-key.json` to version control. These files contain sensitive information. 