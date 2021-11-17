from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_enrollment.db'
app.config['SECRET_KEY'] = 'mysecret'

db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))
    teachers = db.relationship("Teachers", backref="teacher_user_id")
    students = db.relationship("Students", backref="students_user_id")

class Students(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    enrollment = db.relationship("Enrollment", backref="student_user_id")

class Teachers(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    classes = db.relationship("Classes", backref="teacher_user_id")

class Classes(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    course_name = db.Column(db.String(30))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    number_enrolled = db.Column(db.Integer)
    capacity = db.Column(db.Integer)
    start = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    end = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    enrollment = db.relationship("Enrollment", backref="class_enrollment_id")

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    grade = db.Column(db.String(10))





@app.route('/', methods=['GET'])
def index():
    if len(session) > 0:
        user_id = session['id']
        teacher = Teachers.query.filter(Teachers.user_id == user_id).first()
        student = Students.query.filter(Students.user_id == user_id).first()
        if teacher:
            return render_template("index.html", data=data)
        else:            
            enrollment = Enrollment.query.filter(Enrollment.student_id == student.id).all()

            my_course_data = []
            course_data = []
            enrolled_courses = []
            for enroll in enrollment:
                classes = Classes.query.filter(Classes.id == enroll.class_id).first()
                teacher = Teachers.query.filter(Teachers.id == classes.teacher_id).first()

                dic = {"course name": classes.course_name, "teacher": teacher.name, "start": classes.start, "end": classes.end, "students enrolled": classes.number_enrolled, "capacity": classes.capacity, }
                my_course_data.append(dic)
                enrolled_courses.append(classes.course_name)

            courses = Classes.query.all()
            for course in courses:
                enrolled = False
                teacher = Teachers.query.filter(Teachers.id == course.teacher_id).first()
                if course.course_name in enrolled_courses:
                    enrolled = True
                c = {"id": student.id, "class_id": course.id, "course name": course.course_name, "teacher": teacher.name, "start": course.start, "end": course.end, "students enrolled": course.number_enrolled, "enrolled": enrolled, "capacity": course.capacity}
                course_data.append(c)
            
            return render_template("index.html", data=my_course_data, courses=course_data)
    else:
        return redirect(url_for('login'))

@app.route("/enroll/<int:student_id>/<int:class_id>", methods = ['GET'])
def enroll(student_id, class_id):
    enrollment = Enrollment(class_id = class_id, student_id = student_id, grade = 0)
    enrolled_student = Enrollment.query.filter(Enrollment.class_id == class_id).all()
    classes = Classes.query.filter(Classes.id == class_id).first()
    if classes.number_enrolled > classes.capacity:
        return redirect(url_for("index")) 
    classes.number_enrolled = len(enrolled_student) + 1
    db.session.add(classes)
    db.session.add(enrollment)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/unenroll/<int:student_id>/<int:class_id>", methods = ['GET'])
def unenroll(student_id, class_id):
    enrollment = Enrollment.query.filter(Enrollment.class_id == class_id, Enrollment.student_id == student_id).delete()
    enrolled_student = Enrollment.query.filter(Enrollment.class_id == class_id).all()
    classes = Classes.query.filter(Classes.id == class_id).first()
    classes.number_enrolled = len(enrolled_student) - 1
    db.session.add(classes) 
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter(Users.username==username, Users.password==password).first()
        if user:
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            msg = 'Logged in successfully !'
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

admin = Admin(app)

admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(Teachers, db.session))
admin.add_view(ModelView(Students, db.session))
admin.add_view(ModelView(Classes, db.session))
admin.add_view(ModelView(Enrollment, db.session))
if __name__ == '__main__':
    app.run(debug=True)
