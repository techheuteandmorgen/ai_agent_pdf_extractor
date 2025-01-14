from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Relationship with Upload
    uploads = relationship('Upload', backref='user', lazy=True, cascade="all, delete-orphan")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


# Upload Model
class Upload(db.Model):
    __tablename__ = 'upload'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    total_premium = db.Column(db.Float, nullable=True)
    net_premium = db.Column(db.Float, nullable=True)
    commission = db.Column(db.Float, nullable=True)
    upload_date = db.Column(db.DateTime, default=func.now())

    def calculate_commission(self, rate=0.4):
        """Calculate commission based on a rate (default is 40%)."""
        self.commission = (self.total_premium or 0.0) * rate
        return self.commission

    def calculate_net_premium(self):
        """Calculate net premium as total premium minus commission."""
        self.net_premium = (self.total_premium or 0.0) - (self.commission or 0.0)
        return self.net_premium

    def save_to_db(self):
        """Save the upload entry to the database."""
        # Ensure commission and net premium are calculated
        self.calculate_commission()
        self.calculate_net_premium()
        try:
            db.session.add(self)
            db.session.commit()
            print(f"Upload {self.filename} saved successfully.")
        except Exception as e:
            print(f"Error during database commit: {e}")
            db.session.rollback()


# Additional Utility Functions
def initialize_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()