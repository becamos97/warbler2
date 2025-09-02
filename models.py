"""SQLAlchemy models for Warbler."""
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

##############################################################################
# Association Tables

follows = db.Table(
    "follows",
    db.Column("user_being_followed_id", db.Integer, db.ForeignKey("users.id", ondelete="cascade")),
    db.Column("user_following_id", db.Integer, db.ForeignKey("users.id", ondelete="cascade")),
)

likes = db.Table(
    "likes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="cascade")),
    db.Column("message_id", db.Integer, db.ForeignKey("messages.id", ondelete="cascade")),
)

##############################################################################
# Models

class User(db.Model):
    """User in the system."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    image_url = db.Column(db.Text, default="/static/images/default-pic.png")
    header_image_url = db.Column(db.Text, default="/static/images/warbler-hero.jpg")
    bio = db.Column(db.Text)
    location = db.Column(db.Text)
    password = db.Column(db.Text, nullable=False)

    messages = db.relationship("Message", backref="user", cascade="all, delete-orphan")

    followers = db.relationship(
        "User",
        secondary=follows,
        primaryjoin=(follows.c.user_being_followed_id == id),
        secondaryjoin=(follows.c.user_following_id == id),
        backref="following"
    )

    liked_messages = db.relationship(  # <-- unified likes relation
        "Message",
        secondary=likes,
        backref="liked_by"
    )

    def is_following(self, other_user):
        return other_user in self.following

    def is_followed_by(self, other_user):
        return other_user in self.followers

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user. Hashes password and returns user."""
        hashed = bcrypt.generate_password_hash(password).decode("utf8")
        u = cls(username=username, email=email, password=hashed, image_url=image_url)
        db.session.add(u)
        return u

    @classmethod
    def authenticate(cls, username, password):
        """Validate user/password. Return user or False."""
        u = cls.query.filter_by(username=username).first()
        if u and bcrypt.check_password_hash(u.password, password):
            return u
        return False


class Message(db.Model):
    """An individual message (warble)."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(140), nullable=False)  # <-- enforce 140 chars
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="cascade"), nullable=False)

##############################################################################
# Helper functions

def connect_db(app):
    db.app = app
    db.init_app(app)