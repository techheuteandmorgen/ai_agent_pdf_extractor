from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'user'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Define the relationship to the Upload table
    uploads = relationship('Upload', backref='user', lazy=True, cascade="all, delete-orphan")

    # Flask-Login required properties and methods
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        # You can return True here or add logic if you have an "active" column in the model.
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)  # Flask-Login requires the ID to be returned as a string


# Upload Model
class Upload(db.Model):
    __tablename__ = 'upload'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    total_premium = db.Column(db.Float, nullable=True)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())