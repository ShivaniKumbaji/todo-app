from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secure-secret-key"

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = "login"

# -----------------------------
# Models
# -----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300))
    priority = db.Column(db.String(10), default="Medium")
    status = db.Column(db.String(10), default="Pending")
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create DB
with app.app_context():
    db.create_all()

# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form["password"])
        user = User(
            username=request.form["username"],
            password=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.")
        return redirect("/login")

    return render_template("register.html")

# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/")
        flash("Invalid username or password")

    return render_template("login.html")

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# -----------------------------
# Home / Tasks
# -----------------------------
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        task = Task(
            title=request.form["title"],
            description=request.form["description"],
            priority=request.form["priority"],
            status=request.form["status"],
            due_date=datetime.strptime(
                request.form["due_date"], "%Y-%m-%d"
            ) if request.form["due_date"] else None,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash("Task added successfully")
        return redirect("/")

    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)

# -----------------------------
# Update Task
# -----------------------------
@app.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    task = Task.query.get_or_404(id)

    if request.method == "POST":
        task.title = request.form["title"]
        task.description = request.form["description"]
        task.priority = request.form["priority"]
        task.status = request.form["status"]
        task.due_date = datetime.strptime(
            request.form["due_date"], "%Y-%m-%d"
        ) if request.form["due_date"] else None
        db.session.commit()
        return redirect("/")

    return render_template("update.html", task=task)

# -----------------------------
# Delete
# -----------------------------
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect("/")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

