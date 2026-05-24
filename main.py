from tracker import StudentTracker

tracker = StudentTracker()

while True:

    print("\n========== STUDENT GRADE TRACKER ==========")

    print("1. Add Student")
    print("2. Add Grades")
    print("3. View Student Details")
    print("4. Calculate Average")
    print("5. Exit")

    choice = input("Enter your choice: ")

    # ADD STUDENT
    if choice == "1":

        name = input("Enter student name: ")

        roll_number = input("Enter roll number: ")

        tracker.add_student(name, roll_number)

    # ADD GRADES
    elif choice == "2":

        roll_number = input("Enter roll number: ")

        subject = input("Enter subject name: ")

        try:
            grade = float(input("Enter grade: "))

            tracker.add_grades(roll_number, subject, grade)

        except ValueError:
            print("Please enter a valid number.")

    # VIEW DETAILS
    elif choice == "3":

        roll_number = input("Enter roll number: ")

        tracker.view_student_details(roll_number)

    # CALCULATE AVERAGE
    elif choice == "4":

        roll_number = input("Enter roll number: ")

        tracker.calculate_average(roll_number)

    # EXIT
    elif choice == "5":

        print("Exiting program...")

        break

    else:
        print("Invalid choice.")