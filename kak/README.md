# Flask Firebase To-Do List Application

A comprehensive to-do list web application built with Flask, Firebase, and the Quotable API.

## Features

- **User Authentication**: Sign up and login with Firebase Authentication
- **Role-Based Access Control**: Admin and Regular User permissions
- **Task Management**: Create, edit, delete, and mark tasks as complete
- **Image Upload**: Attach images to tasks using Firebase Storage
- **Motivational Quotes**: Daily inspirational quotes from the Quotable API
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Python (Flask)
- **Database**: Firebase Firestore
- **Storage**: Firebase Storage
- **Authentication**: Firebase Authentication
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **API Integration**: Quotable API for motivational quotes

## Project Structure

```
.
├── app/                    # Main application directory
│   ├── __init__.py         # Flask app initialization
│   ├── models/             # Data models
│   │   ├── __init__.py     # Models initialization
│   │   ├── user_model.py   # User model
│   │   ├── admin_model.py  # Admin model
│   │   ├── task_model.py   # Task model
│   │   ├── category_model.py # Category model
│   │   ├── category_task_model.py # CategoryTask model
│   │   └── migrate_admins.py # Migration script
│   ├── routes/             # Route blueprints
│   │   ├── main.py         # Main routes and quote API
│   │   ├── auth.py         # Authentication routes
│   │   └── tasks.py        # Task management routes
│   ├── static/             # Static assets
│   │   ├── css/            # CSS styles
│   │   ├── js/             # JavaScript files
│   │   └── img/            # Image assets
│   └── templates/          # HTML templates
│       ├── base.html       # Base template with layout
│       ├── index.html      # Main dashboard
│       ├── profile.html    # User profile page
│       ├── admin.html      # Admin panel
│       └── modals/         # Modal templates
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # Project documentation
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd todo-app
   ```

2. **Set up Python environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Firebase Setup**:
   - Create a new Firebase project at https://console.firebase.google.com/
   - Set up Authentication (Email/Password and Google Sign-in)
   - Create a Firestore database
   - Set up Firebase Storage
   - Generate a private key for your Firebase Admin SDK
   - Save the private key as `firebase-key.json` in the project root

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Update the Firebase configuration variables

5. **Run the application**:
   ```
   flask run
   ```
   
6. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

## Firebase Firestore Structure

The database has the following collections:

- **users**:
  - Fields: email, taskCount, lastActive, profilePicture, created_at

- **admins**:
  - Fields: userId, active, grantedAt, grantedBy

- **tasks**:
  - Fields: title, description, userId, status, createdAt, imageUrl

- **categories**:
  - Fields: name, color, createdAt

## Models

The application uses an object-oriented approach for its data models:

### User Model
Represents a registered user in the system:
- **Properties**: uid, email, profile_picture, task_count, last_active, created_at
- **Methods**: save(), update(), is_admin(), etc.

### Admin Model
Inherits from the User model and extends it with administrative capabilities:
- **Additional Properties**: admin_id, active, granted_at, granted_by
- **Additional Methods**: deactivate(), create_for_user(), get_all_admins(), etc.

The Admin model inherits all properties and methods from the User model, representing a full "is-a" relationship. This means:
- An Admin is a User with additional privileges
- Admin instances have access to all User methods and properties
- The inheritance approach provides a cleaner object model that matches the real-world relationship

### Category Model
Represents a task category in the system:
- **Properties**: category_id, name, color, created_at
- **Methods**: save(), update(), delete(), get_tasks(), etc.

### Task Model
Inherits from the Category model and extends it with task-specific functionality:
- **Properties**: task_id, title, description, status, user_id, due_date, image_url, created_at, updated_at
- **Methods**: save(), update(), delete(), mark_complete(), attach_image(), etc.

The Task model inherits all properties and methods from the Category model, representing a "is-a" relationship where:
- A Task is a specific type of Category with additional task-specific attributes
- Tasks inherit category properties (name, color) while adding their own specific properties
- The inheritance makes it easy to access category properties directly from a task instance

Data is stored in separate collections for flexibility, but the object models reflect the inheritance relationships.

## API Endpoints

### Authentication

- `POST /auth/register`: Register a new user
- `POST /auth/login`: Login a user
- `POST /auth/logout`: Logout a user
- `PUT /auth/users/<user_id>/role`: Update a user's admin status

### Tasks

- `GET /tasks/`: Get all tasks for the current user
- `POST /tasks/`: Create a new task
- `GET /tasks/<task_id>`: Get a specific task
- `PUT /tasks/<task_id>`: Update a task
- `DELETE /tasks/<task_id>`: Delete a task

### Quotes

- `GET /quote`: Get a random inspirational quote

## Creating an Admin User

To make a user an admin:

1. Login with an existing admin account
2. Go to the Admin Panel
3. Find the user in the users list
4. Check the "Admin Access" checkbox and save

Alternatively, you can manually create an admin record:

1. Go to your Firebase Firestore console
2. Create a new document in the 'admins' collection
3. Set the fields:
   - userId: The UID of the user
   - active: true
   - grantedAt: Current timestamp

### Migrating Existing Admin Users

If you're upgrading from the previous version that used the 'is_admin' flag on user documents, run the migration script:

```
python -m app.models.migrate_admins
```

This will create Admin model records for any users with the is_admin=true flag.

## License

This project is licensed under the MIT License.