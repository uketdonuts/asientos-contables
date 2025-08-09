# Asientos Contables Project

## Overview
Asientos Contables is a Django project designed for managing accounting entries with user authentication features, including mandatory two-factor authentication (2FA). The project utilizes MySQL as the database and implements a user-friendly interface with Bootstrap for a lightweight design.

## Features
- User registration and login
- Password recovery
- Mandatory two-factor authentication (2FA) for all users
- Role-based access control (admin, user)
- Management of accounting entries
- Email confirmation for users with admin roles
- Navigation panel with user avatar and submenu options
- 🛡️ **Ultra-Secure Module**: High-security data management system (authorized personnel only)

## Project Structure
```
asientos-contables
├── asientos_contables
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── users
│   ├── migrations
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── entries
│   ├── migrations
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates
│   ├── base.html
│   ├── users
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── password_reset.html
│   │   └── two_factor_confirm.html
│   └── entries
│       └── list.html
├── static
│   └── css
│       └── style.css
├── requirements.txt
└── README.md
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd asientos-contables
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install `pkg-config` (required for `mysqlclient`):
   ```
   brew install pkg-config
   ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

5. Set up the MySQL database and update the `settings.py` file with your database credentials.

6. Run migrations:
   ```
   python manage.py migrate
   ```

7. Create a superuser for admin access:
   ```
   python manage.py createsuperuser
   ```

8. Start the development server:
   ```
   python manage.py runserver
   ```

## Usage
- Access the application at `http://127.0.0.1:8000/`.
- All users (including administrators) must set up two-factor authentication to use the system.
- After logging in for the first time, you will be automatically redirected to set up 2FA with Google Authenticator or Microsoft Authenticator.
- Use the admin panel to manage users and roles.
- Users can create, edit, and delete accounting entries based on their roles.

## Two-Factor Authentication
The application enforces mandatory two-factor authentication for all users:

1. During registration or first login, users are redirected to set up 2FA.
2. Users must install an authenticator app such as Google Authenticator or Microsoft Authenticator.
3. They must scan the provided QR code or enter the secret key manually.
4. Once configured, users will need to enter a 6-digit code from their authenticator app each time they log in.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License.