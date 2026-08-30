from flask import Flask, render_template, request, redirect, session, flash, jsonify
from database import *
from models import (db, Student, Grade, Admin, Activity)
import joblib
from datetime import timedelta
from datetime import datetime
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from werkzeug.security import (generate_password_hash, check_password_hash)
app = Flask(__name__)
app.secret_key = "student_project_secret"
app.permanent_session_lifetime = timedelta(minutes=30)
from flask import send_file

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer)
from reportlab.lib.styles import (
    getSampleStyleSheet
)
# LOAD ML MODEL
risk_model = joblib.load(
    "academic_risk_model.pkl"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_4Bfu9hIAocQz@ep-spring-paper-ap35peui.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True
}

db.init_app(app)
def log_activity(message):
    activity = Activity(
        activity=message
    )
    db.session.add(activity)
    db.session.commit()
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# AI PERFORMANCE ANALYSIS
def analyze_student_performance(grades):
    if not grades:
        return "No Data", 0, [], []
    total = 0
    weak_subjects = []
    recommendations = []
    for subject, grade in grades:
        total += grade
        # DETECT WEAK SUBJECTS
        if grade < 40:
            weak_subjects.append(subject)
            recommendations.append(
                f"Needs improvement in {subject}"
            )
    average = total / len(grades)
    # PERFORMANCE CLASSIFICATION
    if average >= 80:
        performance = "Excellent"
        recommendations.append(
            "Maintain consistent performance"
        )
    elif average >= 50:
        performance = "Average"
        recommendations.append(
            "Focus more on weak subjects"
        )
    else:
        performance = "At Risk"
        recommendations.append(
            "Requires immediate academic support"
        )
    return (
        performance,
        average,
        weak_subjects,
        recommendations
    )
from sqlalchemy import func
def get_total_students(
        selected_semester="All",
        selected_branch="All"
):

    query = Student.query

    if selected_branch != "All":
        query = query.filter(
            Student.branch == selected_branch
        )

    if selected_semester != "All":

        query = query.join(
            Grade
        ).filter(
            Grade.semester == str(selected_semester)
        )

    return query.distinct().count()

def get_total_subjects():

    return db.session.query(
        Grade.subject
    ).distinct().count()

def get_class_average(
    selected_semester="All",
    selected_branch="All"
):

    query = Grade.query.join(Student)

    if selected_semester != "All":

        query = query.filter(
            Grade.semester == selected_semester
        )

    if selected_branch != "All":

        query = query.filter(
            Student.branch == selected_branch
        )

    average = query.with_entities(
        func.avg(Grade.grade)
    ).scalar()

    if average:

        return round(average, 2)

    return 0

def get_top_performer(
    selected_semester="All",
    selected_branch="All"
):

    query = Student.query

    if selected_branch != "All":

        query = query.filter(
            Student.branch == selected_branch
        )

    students = query.all()

    top_student = None
    top_average = 0

    for student in students:

        if selected_semester == "All":

            grades = student.grades

        else:

            grades = [
                grade
                for grade in student.grades
                if grade.semester == selected_semester
            ]

        if not grades:
            continue

        avg = sum(
            grade.grade
            for grade in grades
        ) / len(grades)

        if avg > top_average:

            top_average = avg
            top_student = student

    return top_student

def get_subject_averages(
    selected_semester="All",
    selected_branch="All"
):

    query = db.session.query(
        Grade.subject,
        func.avg(Grade.grade)
    ).join(Student)

    if selected_semester != "All":

        query = query.filter(
            Grade.semester == selected_semester
        )

    if selected_branch != "All":

        query = query.filter(
            Student.branch == selected_branch
        )

    results = query.group_by(
        Grade.subject
    ).all()

    return [

        {
            "subject": subject,
            "average": round(avg, 2)
        }

        for subject, avg in results

    ]

def get_average_attendance(
    selected_semester="All",
    selected_branch="All"
):

    query = Student.query

    if selected_branch != "All":

        query = query.filter(
            Student.branch == selected_branch
        )

    if selected_semester != "All":

        query = query.join(Grade).filter(
            Grade.semester == selected_semester
        )

    average = query.with_entities(
        func.avg(Student.attendance)
    ).distinct().scalar()

    if average:

        return round(average, 2)

    return 0

def get_low_attendance_count(
    selected_semester="All",
    selected_branch="All"
):

    query = Student.query.filter(
        Student.attendance < 75
    )

    if selected_branch != "All":

        query = query.filter(
            Student.branch == selected_branch
        )

    if selected_semester != "All":

        query = query.join(Grade).filter(
            Grade.semester == selected_semester
        )

    return query.distinct().count()

def get_low_attendance_students(
    selected_semester="All",
    selected_branch="All"
):

    query = Student.query.filter(
        Student.attendance < 75
    )

    if selected_branch != "All":

        query = query.filter(
            Student.branch == selected_branch
        )

    if selected_semester != "All":

        query = query.join(Grade).filter(
            Grade.semester == selected_semester
        )

    return query.distinct().all()

def predict_academic_risk(
    attendance,
    average_marks
):
    # HANDLE EMPTY ATTENDANCE
    if attendance is None:
        attendance = 0
    prediction = risk_model.predict([[attendance, average_marks]])
    return prediction[0]

# CALCULATE GPA
def calculate_gpa(grades):
    if not grades:
        return 0
    total_points = 0
    for grade in grades:
        marks = grade.grade
        # CONVERT MARKS TO GRADE POINTS
        if marks >= 90:
            points = 10
        elif marks >= 80:
            points = 9
        elif marks >= 70:
            points = 8
        elif marks >= 60:
            points = 7
        elif marks >= 50:
            points = 6
        elif marks >= 40:
            points = 5
        else:
            points = 0
        total_points += points
    gpa = total_points / len(grades)
    return round(gpa, 2)

def get_risk_statistics(
    selected_semester="All",
    selected_branch="All"
):
    low = 0
    medium = 0
    high = 0
    query = Student.query
    # BRANCH FILTER
    if selected_branch != "All":
        query = query.filter(
            Student.branch == selected_branch
        )
    students = query.all()
    for student in students:
        # SEMESTER FILTER
        if selected_semester == "All":
            grades = student.grades
        else:
            grades = [
                grade
                for grade in student.grades
                if grade.semester == selected_semester
            ]
        if not grades:
            continue
        average = (
            sum(
                grade.grade
                for grade in grades
            )
            / len(grades)
        )
        risk = predict_academic_risk(
            student.attendance,
            average
        )
        if risk == "Low Risk":
            low += 1
        elif risk == "Medium Risk":
            medium += 1
        else:
            high += 1
    return low, medium, high

def get_top_students(
    selected_semester="All",
    selected_branch="All",
    limit=5
):
    query = Student.query
    # BRANCH FILTER
    if selected_branch != "All":
        query = query.filter(
            Student.branch == selected_branch
        )
    students = query.all()
    leaderboard = []
    for student in students:
        # SEMESTER FILTER
        if selected_semester == "All":
            grades = student.grades
        else:
            grades = [
                grade
                for grade in student.grades
                if grade.semester == selected_semester
            ]
        if not grades:
            continue
        gpa = calculate_gpa(grades)
        leaderboard.append({
            "name": student.name,
            "roll_number": student.roll_number,
            "gpa": gpa
        })
    leaderboard.sort(
        key=lambda x: x["gpa"],
        reverse=True
    )
    return leaderboard[:limit]

# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:

        if session.get("role") == "admin":
            return redirect("/")

        return redirect(
            f"/student/{session['roll_number']}"
        )

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # CHECK ADMIN
        admin = Admin.query.filter_by(
            username=username
        ).first()
        if admin and check_password_hash(
            admin.password,
            password
        ):
            session.permanent = True
            session["user"] = admin.username
            session["role"] = "admin"
            flash("Admin Login Successful!", "success")
            return redirect("/")
        # CHECK STUDENT
        student = Student.query.filter_by(
            username=username
        ).first()
        if student and check_password_hash(
            student.password,
            password
        ):
            session.permanent = True
            session["user"] = student.username
            session["role"] = "student"
            session["roll_number"] = student.roll_number

            flash("Student Login Successful!", "success")
            return redirect(
                f"/student/{student.roll_number}"
            )
        flash(
            "Invalid Username or Password",
            "danger"
        )
        return redirect("/login")
    return render_template("login.html")

# HOME PAGE
@app.route("/")
def home():
    # CHECK LOGIN
    if "user" not in session:
        return redirect("/login")
    selected_semester = request.args.get(
    "semester",
    "All"
    )
    semesters = [
    sem[0]
    for sem in db.session.query(
        Grade.semester
    ).distinct().order_by(
        Grade.semester
    ).all()
    ]
    selected_branch = request.args.get(
    "branch",
    "All"
    )
    branches = [
    branch[0]
    for branch in db.session.query(
        Student.branch
    ).distinct().all()
    ]
    if session.get("role") == "student":
        return redirect(
            f"/student/{session['roll_number']}")
    total_students = get_total_students(
        selected_semester,
        selected_branch
    )
    total_subjects = get_total_subjects()
    class_average = get_class_average(
        selected_semester,
        selected_branch
    )
    top_performer = get_top_performer(
        selected_semester,
        selected_branch
    )
    subject_averages = get_subject_averages(
        selected_semester,
        selected_branch
    )
    average_attendance = get_average_attendance(
        selected_semester,
        selected_branch
    )
    low_attendance = get_low_attendance_count(
        selected_semester,
        selected_branch
    )
    low_attendance_students = get_low_attendance_students(
        selected_semester,
        selected_branch
    )
    low_risk, medium_risk, high_risk = get_risk_statistics(
        selected_semester,
        selected_branch
    )
    top_students = get_top_students(
        selected_semester,
        selected_branch
    )
    recent_activities = Activity.query.order_by(
    Activity.created_at.desc()
    ).limit(10).all()
    return render_template(
        "index.html",
        total_students=total_students,
        total_subjects=total_subjects,
        class_average=class_average,
        top_performer=top_performer,
        subject_averages=subject_averages,
        average_attendance=average_attendance,
        low_attendance=low_attendance,
        low_attendance_students=low_attendance_students,
        low_risk=low_risk,
        medium_risk=medium_risk,
        high_risk=high_risk,
        top_students=top_students,
        selected_semester=selected_semester,
        selected_branch=selected_branch,
        semesters=semesters,
        branches=branches,
        last_updated=datetime.now(),
        recent_activities=recent_activities, )

# VIEW ALL STUDENTS
@app.route("/view_students")
def view_students():
    if "user" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )
    search = request.args.get("search")
    branch = request.args.get("branch", "All")
    section = request.args.get("section", "All")
    message = None
    if search:
        query = Student.query.filter(
            (Student.name.ilike(f"%{search}%")) |
            (Student.roll_number.ilike(f"%{search}%")))
    
        if branch != "All":
            query = query.filter(
                Student.branch == branch)
        if section != "All":
            query = query.filter(
                Student.section == section)
        students = query.all()
        # NO RESULTS

        if not students:
            if search:
                if any(char.isdigit() for char in search):
                    message = "Roll Number not found!"
                else:
                    message = "Student not found!"
            elif branch != "All" or section != "All":
                message = "No students found for the selected filters."
            else:
                message = "No students available."
    else:
        query = Student.query
        if branch != "All":
            query = query.filter(
                Student.branch == branch)
        if section != "All":
            query = query.filter(
                Student.section == section)
        students = query.all()
    return render_template(
        "view_students.html",
        students=students,
        message=message,
        branch=branch,
        section=section
    )
# DELETE STUDENT
@app.route("/delete_student/<roll_number>")
def delete_student(roll_number):
    if "user" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )

    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()
    if student:
        student_name = student.name

        db.session.delete(student)
        db.session.commit()

        log_activity(
            f"🗑️ Student deleted: {student_name} ({roll_number})"
        )

        flash("Student Deleted Successfully!", "danger")
    return redirect("/view_students")
    
# DELETE GRADE
@app.route("/delete_grade/<roll_number>/<subject>")
def delete_grade(roll_number, subject):

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )

    # FIND STUDENT
    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()

    if not student:
        flash("Student not found!", "danger")
        return redirect("/view_students")

    # FIND GRADE
    grade_obj = Grade.query.filter_by(
        student_id=student.id,
        subject=subject
    ).first()

    if grade_obj:
        old_grade = grade_obj.grade

        db.session.delete(grade_obj)
        db.session.commit()

        log_activity(
            f"🗑️ Grade deleted: {student.name} - "
            f"{subject} ({old_grade})"
        )

        flash(
            "Subject Deleted Successfully!",
            "danger"
        )

    else:
        flash(
            "Subject not found!",
            "warning"
        )

    return redirect(f"/student/{roll_number}")

# EDIT GRADE
@app.route("/edit_grade/<roll_number>/<subject>", methods=["GET", "POST"])
def edit_grade(roll_number, subject):

    if "user" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )

    # FIND STUDENT
    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()
    if not student:
        return "Student not found!"
    # FIND GRADE
    grade_obj = Grade.query.filter_by(
        student_id=student.id,
        subject=subject
    ).first()
    if not grade_obj:
        return "Grade not found!"
    # UPDATE
    if request.method == "POST":
        new_grade = float(
            request.form["new_grade"])
        # VALIDATION
        if new_grade < 0 or new_grade > 100:
            flash("Grade must be between 0 and 100","danger" )
            return redirect(
                f"/edit_grade/{roll_number}/{subject}" )
        # UPDATE DATABASE
        old_grade = grade_obj.grade
        grade_obj.grade = new_grade
        db.session.commit()

        log_activity(
            f"✏️ Grade updated: {student.name} - {subject} "
            f"({old_grade} → {new_grade})"
        )
        flash("Grade Updated Successfully!", "warning")

        return redirect(f"/student/{roll_number}" )
    return render_template(
        "edit_grade.html",
        roll_number=roll_number,
        subject=subject,
        current_grade=grade_obj.grade)

# ADD STUDENT
@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if "user" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )
    if request.method == "POST":
        name = request.form["name"].strip().title()
        roll_number = request.form["roll_number"]
        branch = request.form["branch"]
        section = request.form["section"]
        # NAME VALIDATION
        if not name.replace(" ", "").isalpha():
            flash("Name should contain only alphabets!","danger")
            return redirect("/add_student")

        existing_student = Student.query.filter_by(
            roll_number=roll_number
        ).first()

        if existing_student:
            flash("Student already exists!","danger")
            return redirect("/add_student")

        new_student = Student(
            name=name,
            roll_number=roll_number,
            attendance=0,
            branch=branch,
            section=section,
            username=roll_number,
            password=generate_password_hash(roll_number),
            role="student",
            first_login=True)
        db.session.add(new_student)
        db.session.commit()
        log_activity(f"👤 New student added: {name} ({roll_number})")
        flash("Student Added Successfully!", "success")
        return redirect("/")
    return render_template("add_student.html")

# ADD GRADE
@app.route("/add_grade", methods=["GET", "POST"])
def add_grade():

    if "user" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )
    if request.method == "POST":
        roll_number = request.form["roll_number"]
        subject = request.form["subject"].strip().title()
        grade = float(request.form["grade"])
        semester = request.form["semester"]
        # CHECK GRADE RANGE
        if grade < 0 or grade > 100:
            flash("Grade must be between 0 and 100", "danger")
            return redirect("/add_grade")
        # FIND STUDENT
        student = Student.query.filter_by(
            roll_number=roll_number
        ).first()
        # STUDENT NOT FOUND
        if not student:
            flash("Student not found!", "danger")
            return redirect("/add_grade")
        
        # CHECK IF SUBJECT ALREADY EXISTS
        existing_grade = Grade.query.filter_by(
            student_id=student.id,
            subject=subject
        ).first()

        if existing_grade:
            flash(f"{subject} grade already exists for this student!","danger")
            return redirect("/add_grade")
        # CREATE NEW GRADE
        new_grade = Grade(
            student_id=student.id,
            subject=subject,
            grade=grade,
            semester=semester
        )
        db.session.add(new_grade)
        db.session.commit()
        log_activity(f"📘 Grade added: {student.name} - {subject} ({grade})")
        flash("Grade Added Successfully!", "success")
        return redirect(f"/student/{roll_number}")
    return render_template("add_grade.html")
#Get student details
@app.route("/get_student/<roll_number>")
def get_student(roll_number):

    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()

    if student:
        return jsonify({
            "found": True,
            "name": student.name,
            "branch": student.branch,
            "section": student.section
        })

    return jsonify({
        "found": False
    })
# STUDENT PROFILE PAGE
@app.route("/student/<roll_number>")
def student_profile(roll_number):
    if "user" not in session:
        return redirect("/login")
    
    if session.get("role") == "student":
        if session.get("roll_number") != roll_number:
            flash("Access Denied!", "danger")
            return redirect(f"/student/{session['roll_number']}")
    
    # GET STUDENT
    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()

    # STUDENT NOT FOUND
    if not student:
        return "Student not found!"

    # GET GRADES
    grades = student.grades

    # PREPARE DATA FOR AI ANALYSIS
    grade_data = [
        (grade.subject, grade.grade)
        for grade in grades
    ]
    # GROUP GRADES BY SEMESTER
    semester_grades = {}
    for grade in grades:
        if grade.semester not in semester_grades:
            semester_grades[grade.semester] = []
        semester_grades[grade.semester].append(grade)
    # SEMESTER-WISE GPA
    semester_gpas = {}

    for semester, grades_list in semester_grades.items():
        avg_marks = (
            sum(g.grade for g in grades_list)
            / len(grades_list)
        )
        semester_gpas[semester] = round(
            avg_marks / 10,
            2
        )    
    # GPA
    gpa = calculate_gpa(grades)
    # AI ANALYSIS
    (
        performance,
        average,
        weak_subjects,
        recommendations
    ) = analyze_student_performance(grade_data)
    # ML RISK PREDICTION
    risk_prediction = predict_academic_risk(student.attendance, average)
    return render_template(
        "student_profile.html",
        student=student,
        grades=grades,
        semester_grades=semester_grades,
        performance=performance,
        average=average,
        weak_subjects=weak_subjects,
        recommendations=recommendations,
        risk_prediction=risk_prediction,
        semester_gpas=semester_gpas,
        gpa=gpa)

# VIEW STUDENT DETAILS
@app.route("/student_details", methods=["GET", "POST"])
def student_details():

    if request.method == "POST":
        roll_number = request.form["roll_number"]
        student, grades = get_student_details(roll_number)

        if not student:
            return "Student not found!"

        total = 0
        count = 0

        for subject, grade in grades:
            total += grade
            count += 1

        average = total / count if count > 0 else 0

        return render_template(
            "student_details.html",
            student=student,
            grades=grades,
            average=average
        )

    return render_template("student_details.html")
# UPDATE ATTENDANCE
@app.route(
    "/update_attendance/<roll_number>",
    methods=["GET", "POST"]
)
def update_attendance(roll_number):
    if "user" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        flash("Access Denied!", "danger")
        return redirect(
            f"/student/{session['roll_number']}"
        )
    # FIND STUDENT
    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()
    if not student:
        return "Student not found!"
    if request.method == "POST":
        attendance = float(
            request.form["attendance"]
        )
        # VALIDATION
        if attendance < 0 or attendance > 100:
            flash(
                "Attendance must be between 0 and 100",
                "danger"
            )
            return redirect(
                f"/update_attendance/{roll_number}"
            )
        # UPDATE DATABASE
        old_attendance = student.attendance
        student.attendance = attendance
        db.session.commit()

        log_activity(
            f"📅 Attendance updated: {student.name} "
            f"({old_attendance}% → {attendance}%)"
        )

        flash(
            "Attendance Updated Successfully!",
            "success"
        )
        return redirect(
            f"/student/{roll_number}")
    return render_template(
        "update_attendance.html",
        student=student)

# DOWNLOAD STUDENT PDF REPORT
@app.route("/download_report/<roll_number>")
def download_report(roll_number):
    if "user" not in session:
        return redirect("/login")
    # FIND STUDENT
    student = Student.query.filter_by(
        roll_number=roll_number
    ).first()
    if not student:
        return "Student not found!"
    grades = Grade.query.filter_by(
        student_id=student.id
    ).all()
    # CALCULATE AVERAGE
    if grades:
        average = round(
            sum(g.grade for g in grades) / len(grades),
            2
        )
    else:
        average = 0
    # GPA
    gpa = round(average / 10, 2)
    # AI RISK PREDICTION
    risk_prediction = predict_academic_risk(
        student.attendance,
        average
    )
    # AI PERFORMANCE ANALYSIS
    if average >= 85:
        performance = "Excellent"
    elif average >= 70:
        performance = "Good"
    else:
        performance = "Needs Improvement"
    # OVERALL RESULT
    if average >= 40:
        result = "PASS"
    else:
        result = "FAIL"
    # RECOMMENDATIONS
    recommendations = []
    if student.attendance < 75:
        recommendations.append(
            "Improve attendance"
        )
    if average < 60:
        recommendations.append(
            "Focus on weak subjects"
        )
    if average >= 85:
        recommendations.append(
            "Maintain consistent performance"
        )
    if not recommendations:
        recommendations.append(
            "Keep up the good work"
        )
    # PDF FILE NAME
    filename = f"{student.roll_number}_report.pdf"
    # CREATE PDF
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []
    # TITLE
    elements.append(
        Paragraph(
            "STUDENT ANALYTICS HUB",
            styles["Title"]
        )
    )
    elements.append(
        Paragraph(
            "Academic Performance Report",
            styles["Heading2"]
        )
    )
    elements.append(
        Spacer(1, 20)
    )
    # STUDENT INFORMATION
    elements.append(
        Paragraph(
            "Student Information",
            styles["Heading2"]
        )
    )
    elements.append(
        Paragraph(
            f"<b>Name:</b> {student.name}",
            styles["BodyText"]
        )
    )
    elements.append(
        Paragraph(
            f"<b>Roll Number:</b> {student.roll_number}",
            styles["BodyText"]
        )
    )
    elements.append(
    Paragraph(
        f"<b>Branch:</b> {student.branch}",
        styles["BodyText"]
    )
    )

    elements.append(
        Paragraph(
            f"<b>Section:</b> {student.section}",
            styles["BodyText"]
        )
    )
    
    elements.append(Spacer(1, 20))
    # ACADEMIC SUMMARY
    elements.append(
        Paragraph(
            "Academic Summary",
            styles["Heading2"]
        )
    )
    elements.append(
        Paragraph(
            f"<b>Attendance:</b> {student.attendance}%",
            styles["BodyText"]
        )
    )
    elements.append(
        Paragraph(
            f"<b>Average Marks:</b> {average}",
            styles["BodyText"]
        )
    )
    elements.append(
        Paragraph(
            f"<b>GPA:</b> {gpa}",
            styles["BodyText"]
        )
    )
    
    elements.append(
        Paragraph(
            f"<b>AI Academic Risk:</b> {risk_prediction}",
            styles["BodyText"]
        )
    )
    elements.append(Spacer(1, 20))


# SUBJECT PERFORMANCE
    elements.append(
        Paragraph(
            "Semester-wise Subject Performance",
            styles["Heading2"]
        )
    )
    from collections import defaultdict
    # GROUP SUBJECTS BY SEMESTER
    semester_grades = defaultdict(list)
    for grade in grades:
        semester_grades[grade.semester].append(grade)
    # SORT SEMESTERS
    semesters = sorted(semester_grades.keys())
    # PROCESS TWO SEMESTERS AT A TIME
    for i in range(0, len(semesters), 2):
        semester_tables = []
        for semester in semesters[i:i+2]:
            # Semester heading
            semester_title = Paragraph(
                f"Semester {semester}",
                styles["Heading3"]
            )
            table_data = [["Subject", "Marks"]]
            for grade in semester_grades[semester]:
                table_data.append(
                    [
                        grade.subject,
                        str(grade.grade)
                    ]
                )
            sem_table = Table(
                table_data,
                colWidths=[110, 50]
            )
            sem_table.setStyle(
                TableStyle([
                    ("BACKGROUND",(0,0),(-1,0),colors.darkblue),
                    ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                    ("BACKGROUND",(0,1),(-1,-1),colors.beige),
                    ("BOX",(0,0),(-1,-1),1,colors.black),
                    ("GRID",(0,0),(-1,-1),1,colors.black),
                    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                    ("ALIGN",(0,0),(-1,-1),"CENTER"),
                    ("BOTTOMPADDING",(0,0),(-1,0),8)
                ])
            )
            semester_tables.append(
                [semester_title, sem_table]
            )
        # If only one semester remains
        if len(semester_tables) == 1:
            row = [
                semester_tables[0][0],
                "",
            ]
            table_row1 = Table(
                [row],
                colWidths=[220,220]
            )
            elements.append(table_row1)
            row = [
                semester_tables[0][1],
                ""
            ]
            table_row2 = Table(
                [row],
                colWidths=[220,220]
            )
            elements.append(table_row2)
        else:
            # Titles side by side
            title_table = Table(
                [
                    [
                        semester_tables[0][0],
                        semester_tables[1][0]
                    ]
                ],
                colWidths=[220,220]
            )
            elements.append(title_table)
            # Tables side by side
            pair_table = Table(
                [
                    [
                        semester_tables[0][1],
                        semester_tables[1][1]
                    ]
                ],
                colWidths=[220,220]
            )
            elements.append(pair_table)
        elements.append(
            Spacer(1,15)
        )
    # RECOMMENDATIONS
    elements.append(
        Paragraph(
            "Recommendations",
            styles["Heading2"]
        )
    )
    for rec in recommendations:
        elements.append(
            Paragraph(
                f"• {rec}",
                styles["BodyText"]
            )
        )
    elements.append(Spacer(1,20))
    # OVERALL RESULT
    elements.append(
        Paragraph(
            "Overall Result",
            styles["Heading2"]
        )
    )
    if result == "PASS":
        result_color = colors.green
    else:
        result_color = colors.red
    result_table = Table(
        [
            ["Result", result]
        ],
        colWidths=[150,150]
    )
    result_table.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.lightgrey),
            ("BACKGROUND",(1,0),(1,0),result_color),
            ("TEXTCOLOR",(1,0),(1,0),colors.white),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
            ("BOX",(0,0),(-1,-1),1,colors.black),
            ("GRID",(0,0),(-1,-1),1,colors.black),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("BOTTOMPADDING",(0,0),(-1,-1),8)
        ])
    )
    elements.append(result_table)
    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            f"Generated On: {datetime.now().strftime('%d-%m-%Y')}",
            styles["BodyText"]
        )
    )
    elements.append(
    Spacer(1,10)
    )

    line = Table(
        [[""]],
        colWidths=[450]
    )

    line.setStyle(
        TableStyle([
            ("LINEABOVE",(0,0),(-1,-1),1,colors.grey)
        ])
    )

    elements.append(line)

    elements.append(
        Spacer(1,5)
    )
    # FOOTER
    elements.append(
    Paragraph(
        "Generated by Student Analytics Hub | AI-Powered Academic Performance System",
        styles["Italic"]
    )
    )
    # BUILD PDF
    doc.build(elements)

    return send_file(
        filename,
        as_attachment=True
    )

#Change password
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        if session.get("role") == "admin":
            user = Admin.query.filter_by(username=session["user"]).first()
        else:
            user = Student.query.filter_by(username=session["user"]).first()
        # VERIFY CURRENT PASSWORD
        if not check_password_hash(user.password,current_password):
            flash("Current password is incorrect!", "danger")           
            return redirect("/change_password")
        # MATCH NEW PASSWORDS
        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")            
            return redirect("/change_password")
        # MINIMUM LENGTH
        if len(new_password) < 6:
            flash("Password must be at least 6 characters!", "danger")
            return redirect("/change_password")
        # UPDATE PASSWORD
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Password changed successfully!", "success")
        return redirect("/")
    return render_template(
        "change_password.html"
    )
# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged Out Successfully!", "info")
    return redirect("/login")
with app.app_context():
    db.create_all()
    print("Tables created successfully!")
if __name__ == "__main__":
    app.run(debug=True)