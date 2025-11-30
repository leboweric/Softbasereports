"""
Currie Cloud Platform Configuration
All settings loaded from environment variables for security.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # PostgreSQL (Railway)
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/currie_cloud')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # Encryption key for storing dealer database credentials
    CREDENTIAL_ENCRYPTION_KEY = os.environ.get('CREDENTIAL_ENCRYPTION_KEY', '')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestConfig
    }
    return configs.get(env, DevelopmentConfig)
