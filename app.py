from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

# Project table
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# Task table
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            return "Login Successful 🎉"
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    tasks = Task.query.all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == 'Done'])
    pending = len([t for t in tasks if t.status == 'Pending'])

    return render_template('dashboard.html',
                           tasks=tasks,
                           total=total,
                           completed=completed,
                           pending=pending)

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        name = request.form['name']
        project = Project(name=name)
        db.session.add(project)
        db.session.commit()
        return redirect('/dashboard')

    return render_template('create_project.html')

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    users = User.query.all()

    if request.method == 'POST':
        title = request.form['title']
        user_id = request.form['user_id']

        task = Task(title=title, user_id=user_id)
        db.session.add(task)
        db.session.commit()

        return redirect('/dashboard')

    return render_template('create_task.html', users=users)

@app.route('/update_task/<int:id>')
def update_task(id):
    task = Task.query.get(id)
    if task.status == 'Pending':
        task.status = 'Done'
    else:
        task.status = 'Pending'

    db.session.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # creates database
    app.run(debug=True)