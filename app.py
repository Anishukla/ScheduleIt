from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, DateField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date
from sqlalchemy import update
import os

app = Flask(__name__)
file_path = os.path.abspath(os.getcwd())+"/database.db"
app.config['SECRET_KEY'] = 'hey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+file_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    WorkType = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False, default='NEW')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message="Invalid Email"),  Length(max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    content = TextAreaField('Description')
    priority = SelectField('Priority', choices=[('Low','Low'), ('Medium', 'Medium'), ('High','High')], default='High')
    date = DateField('DeadLine', validators=[InputRequired()])
    WorkType = SelectField('Work-Type', choices=[('Personal','Personal'), ('Work', 'Work'), ('Others','Others')], default='Others')
    Other = StringField('WorkType (If Others)')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid Username or password</h1>'

    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id)
    return render_template('dashboard.html', tasks= tasks, name=current_user.username, tdate=date.today())

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password= hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))


    return render_template('signup.html', form=form)


@app.route('/addtask', methods=['GET', 'POST'])
@login_required
def addtask():
    form = TaskForm()
    tdate=form.date.data
    if form.validate_on_submit():
        if tdate < date.today() :
            flash('Your task has not been created!')
            return render_template('addtask.html', title='New Task', form=form, legend='New Task', name=current_user.username)
        if form.WorkType.data == 'Others':
            new_task = Task(title=form.title.data, content=form.content.data, priority = form.priority.data, date = form.date.data, WorkType = form.Other.data, author=current_user)
        else:
            new_task = Task(title=form.title.data, content=form.content.data, priority = form.priority.data, date = form.date.data, WorkType = form.WorkType.data, author=current_user)
        db.session.add(new_task)
        db.session.commit()
        flash('Your task has been created!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('addtask.html', title='New Task', form=form, legend='New Task', name=current_user.username)


@app.route('/personaltask', methods=['GET', 'POST'])
@login_required
def personaltask():
    tasks = Task.query.filter_by(user_id=current_user.id)
    return render_template('personal.html', tasks=tasks ,name=current_user.username, tdate=date.today())


@app.route('/worktask', methods=['GET', 'POST'])
@login_required
def worktask():
    tasks = Task.query.filter_by(user_id=current_user.id)
    return render_template('work.html', tasks=tasks ,name=current_user.username, tdate=date.today())


@app.route('/othertask', methods=['GET', 'POST'])
@login_required
def othertask():
    tasks = Task.query.filter_by(user_id=current_user.id)
    return render_template('other.html', tasks=tasks ,name=current_user.username, tdate=date.today())

@app.route("/<int:task_id>/update", methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        status_u = request.form['STATUS']
        task_status=Task.query.filter_by(user_id=current_user.id, id=task_id).update({Task.status: status_u})
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('checktask.html', title='Update Task', task=task, legend='Update Task', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
