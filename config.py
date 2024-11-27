import os
from dotenv import load_dotenv
import urllib

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database configuration
    SERVER = os.getenv('DB_SERVER')
    USERNAME = os.getenv('DB_USERNAME')
    PASSWORD = os.getenv('DB_PASSWORD')
    DRIVER = os.getenv('DB_DRIVER')

    # Email configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')
    
    # Gmail API configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_SUBJECT_PREFIX = os.getenv('MAIL_SUBJECT_PREFIX', '[Canvassed]')

    # Frontend URL (for email confirmation links)
    FRONTEND_URL = os.getenv('FRONTEND_URL')

    @staticmethod
    def get_database_uri(database_name):
        params = urllib.parse.quote_plus(
            f'DRIVER={Config.DRIVER};SERVER={Config.SERVER};DATABASE={database_name};UID={Config.USERNAME};PWD={Config.PASSWORD}'
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"

    @staticmethod
    def get_listings_database_uri():
        params = urllib.parse.quote_plus(
            f'DRIVER={Config.DRIVER};SERVER={Config.SERVER};DATABASE={os.getenv("LISTINGS_DB_NAME")};UID={Config.USERNAME};PWD={Config.PASSWORD}'
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE = os.getenv('DEV_DB_NAME')
    SQLALCHEMY_DATABASE_URI = Config.get_database_uri(DATABASE)
    SQLALCHEMY_BINDS = {
        'listings': Config.get_listings_database_uri()
    }

class ProductionConfig(Config):
    DEBUG = False
    DATABASE = os.getenv('PROD_DB_NAME')
    SQLALCHEMY_DATABASE_URI = Config.get_database_uri(DATABASE)
    SQLALCHEMY_BINDS = {
        'listings': Config.get_listings_database_uri()
    }
    # FRONTEND_URL = os.getenv('PROD_FRONTEND_URL')  # Add this for production

class StagingConfig(Config):
    DEBUG = True
    DATABASE = os.getenv('STAGING_DB_NAME')
    SQLALCHEMY_DATABASE_URI = Config.get_database_uri(DATABASE)
    FRONTEND_URL = os.getenv('STAGING_FRONTEND_URL')  # Add this for staging
    SQLALCHEMY_BINDS = {
        'listings': Config.get_listings_database_uri()
    }
