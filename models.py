from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
db = SQLAlchemy()


class Student(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    roll_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    attendance = db.Column(
        db.Float,
        default=0
    )

    username = db.Column(
    db.String(100),
    unique=True
    )

    password = db.Column(
        db.String(300)
    )

    role = db.Column(
        db.String(20),
        default="student"
    )

    first_login = db.Column(
        db.Boolean,
        default=True
    )
    grades = db.relationship(
        "Grade",
        backref="student",
        cascade="all, delete",
        lazy=True
    )
    branch = db.Column(
    db.String(50)
    )

    section = db.Column(
        db.String(10)
    )

class Grade(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    grade = db.Column(
        db.Float,
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )

    semester = db.Column(
    db.String(20),
    default="1"
    )

class Admin(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(300),
        nullable=False
    )
from datetime import datetime

class Activity(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    activity = db.Column(
        db.String(300),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
    )