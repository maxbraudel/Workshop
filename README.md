# Cinemacousas - Movie Reservation System

A modern Flask-based movie reservation system with user authentication, session management, and a responsive UI.

## 🚀 Features

- **User Authentication**: Secure registration and login system
- **Session Management**: Automatic session cleanup and validation
- **Responsive Design**: Mobile-friendly interface with Bootstrap
- **Database Connection Pooling**: Optimized database performance
- **Error Handling**: Custom error pages and comprehensive logging
- **Environment Configuration**: Secure configuration management
- **Background Tasks**: Automated maintenance tasks

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: Bootstrap 5, Font Awesome
- **Session Management**: Flask sessions with database storage
- **Background Tasks**: APScheduler
- **Logging**: Python logging with file rotation

## 📋 Prerequisites

- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Workshop
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   FLASK_SECRET_KEY=your-super-secret-key-here
   FLASK_ENV=development
   FLASK_DEBUG=True
   
   DB_HOST=your-database-host
   DB_PORT=3306
   DB_USER=your-username
   DB_PASSWORD=your-password
   DB_NAME=your-database-name
   ```

5. **Set up the database**
   - Create a MySQL database
   - Import your database schema
   - Update the database configuration in `.env`

6. **Run the application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5500`

## 📁 Project Structure

```
Workshop/
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Environment variables (create from .env.example)
├── .gitignore            # Git ignore rules
├── src/                  # Source code
│   ├── config.py         # Configuration management
│   ├── middleware.py     # Request middleware and decorators
│   ├── session_manager.py # Background session management
│   ├── error_handlers.py # Error handling
│   ├── logging_config.py # Logging configuration
│   └── database/         # Database modules
│       ├── __init__.py
│       ├── database.py          # Core database functionality
│       ├── database_retrieve.py # Data retrieval functions
│       ├── database_validate.py # Data validation functions
│       └── database_modify.py   # Data modification functions
├── templates/            # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── movies.html
│   ├── navbar.html
│   └── errors/           # Error pages
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
├── static/              # Static files
│   ├── css/
│   │   ├── styles.css
│   │   └── reset.css
│   └── images/
└── logs/               # Application logs (created automatically)
```

## 🔒 Security Features

- **Environment Variables**: Sensitive data stored in environment variables
- **Database Connection Pooling**: Prevents connection exhaustion
- **Session Validation**: Automatic session validation and cleanup
- **Password Hashing**: Secure password storage with Werkzeug
- **CSRF Protection**: Built-in Flask session protection
- **Input Validation**: Comprehensive form validation

## 🚀 Deployment

### Production Configuration

1. **Update environment variables**
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   FLASK_SECRET_KEY=your-production-secret-key
   ```

2. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Set up reverse proxy** (nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 📊 Database Schema

The application expects the following database tables:

- `account`: User account information
- `account_session`: User session tracking
- `movie`: Movie information

## 🔧 Configuration Options

All configuration is handled through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Flask session secret key | Required |
| `FLASK_ENV` | Environment (development/production) | development |
| `FLASK_DEBUG` | Debug mode | True |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 3306 |
| `DB_USER` | Database username | root |
| `DB_PASSWORD` | Database password | (empty) |
| `DB_NAME` | Database name | cinemacousas |
| `DB_POOL_SIZE` | Connection pool size | 10 |
| `SESSION_LIFETIME_HOURS` | Session validity period | 24 |

## 🐛 Debugging

1. **Enable debug mode**
   ```env
   FLASK_DEBUG=True
   FLASK_ENV=development
   ```

2. **Check logs**
   ```bash
   tail -f logs/cinema.log
   ```

3. **Database connection issues**
   - Verify database credentials in `.env`
   - Check if database server is running
   - Ensure database exists and is accessible

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:

1. Check the logs in the `logs/` directory
2. Verify your environment configuration
3. Ensure all dependencies are installed
4. Check database connectivity

For additional help, please open an issue in the repository.
