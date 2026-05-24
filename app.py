from flask import Flask, render_template, request, redirect, session, flash
from database import *

app = Flask(__name__)
app.secret_key = "student_project_secret"

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
# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # SIMPLE ADMIN LOGIN
        if username == "admin" and password == "admin123":

            session["user"] = username
            flash("Login Successful!", "success")
            return redirect("/")

        else:

            flash("Invalid Username or Password", "danger")
            return redirect("/login")

    return render_template("login.html")

# HOME PAGE
@app.route("/")
def home():
    # CHECK LOGIN
    if "user" not in session:
        return redirect("/login")

    total_students = get_total_students()
    total_subjects = get_total_subjects()
    class_average = get_class_average()
    top_performer = get_top_performer()
    subject_averages = get_subject_averages()

    return render_template(
        "index.html",
        total_students=total_students,
        total_subjects=total_subjects,
        class_average=class_average,
        top_performer=top_performer,
        subject_averages=subject_averages
    )

# VIEW ALL STUDENTS
@app.route("/view_students")
def view_students():
    search = request.args.get("search")

    if search:
        cursor.execute("""
        SELECT * FROM students
        WHERE name LIKE ? OR roll_number LIKE ?
        """, (f"%{search}%", f"%{search}%"))

        students = cursor.fetchall()
    else:
        students = get_all_students()

    return render_template(
        "view_students.html",
        students=students
    )

# DELETE STUDENT
@app.route("/delete_student/<roll_number>")
def delete_student(roll_number):
    delete_student_db(roll_number)

    flash("Student Deleted Successfully!", "danger")
    return redirect("/view_students")

# DELETE SUBJECT
@app.route("/delete_subject/<roll_number>/<subject>")
def delete_subject(roll_number, subject):
    delete_subject_db(
        roll_number,
        subject
    )
    flash("Subject Deleted Successfully!", "danger")
    return redirect(f"/student/{roll_number}")

# EDIT GRADE
@app.route("/edit_grade/<roll_number>/<subject>", methods=["GET", "POST"])
def edit_grade(roll_number, subject):

    if request.method == "POST":
        new_grade = float(request.form["new_grade"])
        # VALIDATION
        if new_grade < 0 or new_grade > 100:
            flash("Grade must be between 0 and 100", "danger")
        update_grade_db(
            roll_number,
            subject,
            new_grade
        )

        return redirect(f"/student/{roll_number}")
    return render_template(
        "edit_grade.html",
        roll_number=roll_number,
        subject=subject
    )

# UPDATE GRADE
@app.route("/update_grade", methods=["GET", "POST"])
def update_grade():

    if request.method == "POST":
        roll_number = request.form["roll_number"]
        subject = request.form["subject"].strip().title()
        new_grade = float(request.form["new_grade"])

        # VALIDATION
        if grade < 0 or grade > 100:
            flash("Grade must be between 0 and 100", "danger")
            return redirect(f"/edit_grade/{roll_number}/{subject}")

        update_grade_db(
            roll_number,
            subject,
            new_grade
        )
        flash("Grade Updated Successfully!", "warning")
        return redirect(f"/student/{roll_number}")
    return render_template("update_grade.html")

# ADD STUDENT
@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":
        name = request.form["name"]
        roll_number = request.form["roll_number"]

        if student_exists(roll_number):
            flash("Student already exists!", "danger")
            return redirect("/add_student")

        add_student_db(name, roll_number)

        flash("Student Added Successfully!", "success")
        return redirect("/")
    return render_template("add_student.html")

# ADD GRADE
@app.route("/add_grade", methods=["GET", "POST"])
def add_grade():

    if request.method == "POST":
        roll_number = request.form["roll_number"]
        subject = request.form["subject"].strip().title()
        grade = float(request.form["grade"])

        if grade < 0 or grade > 100:
            flash("Grade must be between 0 and 100", "danger")
            return redirect("/add_grade")

        if not student_exists(roll_number):
            flash("Student not found!")
            return redirect("/add_grade")

        add_grade_db(roll_number, subject, grade)
        flash("Grade Added Successfully!", "success")
        return redirect("/")

    return render_template("add_grade.html")

# STUDENT PROFILE PAGE
@app.route("/student/<roll_number>")
def student_profile(roll_number):

    student, grades = get_student_details(roll_number)

    if not student:

        return "Student not found!"

    # AI ANALYSIS
    (
    performance,
    average,
    weak_subjects,
    recommendations) = analyze_student_performance(grades)

    return render_template(
    "student_profile.html",
    student=student,
    grades=grades,
    performance=performance,
    average=average,
    weak_subjects=weak_subjects,
    recommendations=recommendations)

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
# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)
    flash("Logged Out Successfully!", "info")
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)