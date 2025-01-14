from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

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
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def calculate_commission(self, rate=0.4):
        self.commission = self.total_premium * rate if self.total_premium else 0.0
        return self.commission

    def calculate_net_premium(self):
        self.net_premium = self.total_premium - (self.commission or 0.0) if self.total_premium else 0.0
        return self.net_premium

    def save_to_db(self):
        self.calculate_commission()
        self.calculate_net_premium()
        db.session.add(self)
        db.session.commit()
