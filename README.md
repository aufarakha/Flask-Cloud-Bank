# Flask Cloud Bank

A modern banking web application built with Flask, featuring user authentication, money transfers, transaction history, and admin panel.

[Baca dalam Bahasa Indonesia](README_ID.md)

## Features

- User authentication and registration
- Money transfers between accounts
- Transaction history tracking
- Real-time currency exchange rates
- Admin panel for user management
- Multi-language support (English/Indonesian)
- Dark/Light mode toggle
- Profile photo management

## Installation

1. Clone the repository:

```bash
git clone https://github.com/aufarakha/Flask-Cloud-Bank.git
cd Flask-Cloud-Bank
```

2. Create a virtual environment and activate it:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your Exchange Rate API key:

```
EXCHANGE_API_KEY=your_api_key_here
```

5. Initialize the database:

```bash
python db_setup.py
```

6. Run the application:

```bash
python app.py
```

7. Access the application at `http://localhost:5000`

Default owner account:

- Email: owner@cloudbank.com
- Password: ownerpass

## Project Structure

```
Flask-Cloud-Bank/
├── app.py              # Main application file
├── models.py           # Database models
├── db_setup.py         # Database initialization
├── requirements.txt    # Project dependencies
├── static/            # Static files (CSS, JS, images)
├── templates/         # HTML templates
└── instance/         # SQLite database
```

## Tech Stack

- Flask - Web framework
- SQLAlchemy - Database ORM
- Flask-Login - User authentication
- SQLite - Database
- Exchange Rate API - Currency conversion

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
