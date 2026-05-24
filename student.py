class Student:
    def __init__(self, name, roll_number):
        self.name = name
        self.roll_number = roll_number
        self.grades = {}

    def add_grade(self, subject, grade):
        if 0 <= grade <= 100:
            self.grades[subject] = grade
            print("Grade added successfully.")
        else:
            print("Grade must be between 0 and 100.")

    def calculate_average(self):
        if len(self.grades) == 0:
            return 0

        total = sum(self.grades.values())
        average = total / len(self.grades)

        return average

    def display_info(self):
        print("\n===== Student Details =====")
        print("Name:", self.name)
        print("Roll Number:", self.roll_number)

        print("\nGrades:")

        if len(self.grades) == 0:
            print("No grades available.")
        else:
            for subject, grade in self.grades.items():
                print(subject, ":", grade)

        print("Average Grade:", round(self.calculate_average(), 2))