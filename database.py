import sqlite3
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from models import Student, Grade

db = SQLAlchemy()
# CONNECT DATABASE
conn = sqlite3.connect("students.db", check_same_thread=False)

# CURSOR OBJECT
cursor = conn.cursor()

# CREATE STUDENTS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    name TEXT,
    roll_number TEXT PRIMARY KEY
)
""")

# CREATE GRADES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS grades (
    roll_number TEXT,
    subject TEXT,
    grade REAL
)
""")

conn.commit()

# ADD STUDENT
def add_student_db(name, roll_number):

    cursor.execute("""
    INSERT INTO students (name, roll_number)
    VALUES (?, ?)
    """, (name, roll_number))

    conn.commit()


# CHECK STUDENT EXISTS
def student_exists(roll_number):

    cursor.execute("""
    SELECT * FROM students
    WHERE roll_number = ?
    """, (roll_number,))

    return cursor.fetchone()


# ADD GRADE
def add_grade_db(roll_number, subject, grade):

    # CHECK IF SUBJECT ALREADY EXISTS
    if subject_exists(roll_number, subject):

        # UPDATE EXISTING GRADE
        cursor.execute("""
        UPDATE grades
        SET grade = ?
        WHERE roll_number = ? AND subject = ?
        """, (grade, roll_number, subject))

    else:

        # INSERT NEW SUBJECT
        cursor.execute("""
        INSERT INTO grades (roll_number, subject, grade)
        VALUES (?, ?, ?)
        """, (roll_number, subject, grade))

    conn.commit()

# GET STUDENT DETAILS
def get_student_details(roll_number):

    cursor.execute("""
    SELECT * FROM students
    WHERE roll_number = ?
    """, (roll_number,))

    student = cursor.fetchone()

    cursor.execute("""
    SELECT subject, grade FROM grades
    WHERE roll_number = ?
    """, (roll_number,))

    grades = cursor.fetchall()

    return student, grades

# GET ALL STUDENTS
def get_all_students():

    cursor.execute("""
    SELECT * FROM students
    """)

    return cursor.fetchall()

# DELETE STUDENT
def delete_student_db(roll_number):

    # DELETE GRADES FIRST
    cursor.execute("""
    DELETE FROM grades
    WHERE roll_number = ?
    """, (roll_number,))

    # DELETE STUDENT
    cursor.execute("""
    DELETE FROM students
    WHERE roll_number = ?
    """, (roll_number,))

    conn.commit()

# UPDATE GRADE
def update_grade_db(roll_number, subject, new_grade):

    cursor.execute("""
    UPDATE grades
    SET grade = ?
    WHERE roll_number = ? AND subject = ?
    """, (new_grade, roll_number, subject))

    conn.commit()

# CHECK SUBJECT EXISTS
def subject_exists(roll_number, subject):

    cursor.execute("""
    SELECT * FROM grades
    WHERE roll_number = ? AND subject = ?
    """, (roll_number, subject))

    return cursor.fetchone()

# DELETE SUBJECT GRADE
def delete_subject_db(roll_number, subject):

    cursor.execute("""
    DELETE FROM grades
    WHERE roll_number = ? AND subject = ?
    """, (roll_number, subject))

    conn.commit()

# TOTAL STUDENTS
def get_total_students():

    cursor.execute("""
    SELECT COUNT(*) FROM students
    """)

    return cursor.fetchone()[0]

# TOTAL SUBJECTS
def get_total_subjects():

    cursor.execute("""
    SELECT COUNT(DISTINCT LOWER(subject)) FROM grades
    """)

    return cursor.fetchone()[0]

# CLASS AVERAGE
def get_class_average():

    cursor.execute("""
    SELECT AVG(grade) FROM grades
    """)

    result = cursor.fetchone()[0]

    return round(result, 2) if result else 0

# TOP PERFORMER
from sqlalchemy import func

def get_top_performer():

    top_student = db.session.query(
        Student,
        func.avg(Grade.grade).label("average")
    ).join(
        Grade,
        Student.id == Grade.student_id
    ).group_by(
        Student.id
    ).order_by(
        func.avg(Grade.grade).desc()
    ).first()

    if top_student:
        return top_student[0]

    return None

# SUBJECT AVERAGES
def get_subject_averages():

    cursor.execute("""
    SELECT LOWER(subject),
           AVG(grade)

    FROM grades

    GROUP BY LOWER(subject)
    """)

    return cursor.fetchall()