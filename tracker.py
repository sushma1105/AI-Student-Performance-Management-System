from database import *

class StudentTracker:

    def add_student(self, name, roll_number):

        if student_exists(roll_number):

            print("Student already exists.")

        else:
            add_student_db(name, roll_number)

            print("Student added successfully.")

    def add_grades(self, roll_number, subject, grade):

        if student_exists(roll_number):

            if 0 <= grade <= 100:

                add_grade_db(roll_number, subject, grade)

                print("Grade added successfully.")

            else:
                print("Grade must be between 0 and 100.")

        else:
            print("Student not found.")

    def view_student_details(self, roll_number):

        student, grades = get_student_details(roll_number)

        if student:

            print("\n===== STUDENT DETAILS =====")

            print("Name:", student[0])

            print("Roll Number:", student[1])

            print("\nGrades:")

            total = 0

            count = 0

            for subject, grade in grades:

                print(subject, ":", grade)

                total += grade

                count += 1

            if count > 0:

                average = total / count

                print("\nAverage Grade:", round(average, 2))

            else:
                print("No grades available.")

        else:
            print("Student not found.")