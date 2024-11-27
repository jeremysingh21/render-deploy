# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from config import DevelopmentConfig, ProductionConfig, StagingConfig

app = Flask(__name__)
CORS(app)

# Configure the app based on environment
env = os.getenv('FLASK_ENV', 'development')
if env == 'production':
    app.config.from_object(ProductionConfig)
elif env == 'staging':
    app.config.from_object(StagingConfig)
else:
    app.config.from_object(DevelopmentConfig)

db = SQLAlchemy(app)

# User model
class User(db.Model):
    __tablename__ = 'users_react'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)

@app.route('/api/users')
def get_users():
    try:
        users = User.query.limit(5).all()
        users_list = [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]
        return jsonify({'users': users_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api')
def hello_world():
    return jsonify({'message': 'Hello from Flask backend!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
