import os
print("TEMPLATE FOLDER:", os.path.abspath("templates"))

from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ---------------- HELPER FUNCTION ---------------- #

def update_overdue_tasks():
    today = datetime.today().strftime('%Y-%m-%d')

    tasks = Task.query.all()

    for task in tasks:
        if task.deadline < today and task.status != 'Done':
            task.status = 'Overdue'

    db.session.commit()

app = Flask(__name__)

app.secret_key = "anything123"

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))   # hr / employee


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Pending')
    priority = db.Column(db.String(20))
    deadline = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return render_template('home.html')


# -------- SIGNUP -------- #

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        new_user = User(
            username=username,
            password=password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('signup.html')


# -------- LOGIN -------- #

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:

            session['user_id'] = user.id
            session['role'] = user.role

            # HR LOGIN
            if user.role == 'hr':
                return redirect('/hr_dashboard')

            # EMPLOYEE LOGIN
            else:
                return redirect('/dashboard')

        else:
            return "Invalid credentials"

    return render_template('login.html')


# -------- EMPLOYEE DASHBOARD -------- #

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    update_overdue_tasks()

    filter_status = request.args.get('status', 'all')

    query = Task.query.filter_by(user_id=session['user_id'])

    if filter_status != 'all':
        query = query.filter_by(status=filter_status)

    tasks = query.all()

    total = Task.query.filter_by(user_id=session['user_id']).count()

    completed = Task.query.filter_by(user_id=session['user_id'], status='Done').count()

    pending = Task.query.filter_by(user_id=session['user_id'], status='Pending').count()

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        role=session['role'],
        selected_filter=filter_status
    )

# -------- HR DASHBOARD -------- #

@app.route('/hr_dashboard', methods=['GET', 'POST'])
def hr_dashboard():

    if 'user_id' not in session or session['role'] != 'hr':
        return redirect('/login')

    users = User.query.filter_by(role='employee').all()

    # ---------------- ASSIGN TASK ---------------- #
    if request.method == 'POST':

        title = request.form.get('title')
        deadline = request.form.get('deadline')
        user_id = request.form.get('user_id')

        priority = "Low"

        if "urgent" in title.lower() or "critical" in title.lower():
            priority = "High"
        elif "meeting" in title.lower() or "presentation" in title.lower():
            priority = "Medium"

        new_task = Task(
            title=title,
            user_id=user_id,
            status='Pending',
            priority=priority,
            deadline=deadline
        )

        db.session.add(new_task)
        db.session.commit()

    # ---------------- FILTER LOGIC ---------------- #
    status_filter = request.args.get('status', 'all')

    query = db.session.query(Task, User).join(User, Task.user_id == User.id)

    if status_filter != 'all':
        query = query.filter(Task.status == status_filter)

    tasks = query.all()

    # ---------------- STATS ---------------- #
    employee_stats = []

    employees = User.query.filter_by(role='employee').all()

    for employee in employees:

        total = Task.query.filter_by(user_id=employee.id).count()

        completed = Task.query.filter_by(user_id=employee.id, status='Done').count()

        percentage = int((completed / total) * 100) if total > 0 else 0

        if percentage >= 80:
            performance = "Excellent"
        elif percentage >= 50:
            performance = "Good"
        else:
            performance = "Needs Improvement"

        employee_stats.append({
            'name': employee.username,
            'percentage': percentage,
            'performance': performance
        })

    # ---------------- ANALYTICS ---------------- #
    total_employees = User.query.filter_by(role='employee').count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='Done').count()
    pending_tasks = Task.query.filter_by(status='Pending').count()
    overdue_tasks = Task.query.filter_by(status='Overdue').count()

    return render_template(
        'hr_dashboard.html',
        users=users,
        tasks=tasks,
        total_employees=total_employees,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        employee_stats=employee_stats,
        selected=status_filter
    )

# -------- UPDATE TASK -------- #

@app.route('/update_task/<int:id>')
def update_task(id):

    task = Task.query.get(id)

    if task:

        if task.status == 'Pending':
            task.status = 'Done'

        else:
            task.status = 'Pending'

        db.session.commit()

    return redirect('/dashboard')


# -------- DELETE TASK -------- #

@app.route('/delete_task/<int:id>')
def delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)
    db.session.commit()

    return redirect('/hr_dashboard')


# -------- LOGOUT -------- #

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# -------- RUN APP -------- #
def init_db():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":

    init_db()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)