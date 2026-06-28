from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    prompts = db.relationship("Prompt", backref="user", lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship("ContentTask", backref="user", lazy=True, cascade="all, delete-orphan")


class Prompt(db.Model):
    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False, default="Other")
    platform = db.Column(db.String(80), nullable=False, default="Other")
    main_prompt = db.Column(db.Text, nullable=False)
    negative_prompt = db.Column(db.Text)
    aspect_ratio = db.Column(db.String(20))
    visual_style = db.Column(db.String(80))
    rating = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tasks = db.relationship("ContentTask", backref="prompt", lazy=True, passive_deletes=True)


class ContentTask(db.Model):
    __tablename__ = "content_tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(160), nullable=False)
    content_type = db.Column(db.String(40), nullable=False, default="Image")
    status = db.Column(db.String(40), nullable=False, default="Ide")
    due_date = db.Column(db.Date)
    platform = db.Column(db.String(80), nullable=False, default="Other")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
