from flask import Flask, render_template, request, redirect, url_for, session, send_file
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import random
import os
import glob
import time
from utils.pdf_generator import create_pdf

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///database.db'
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100), unique=True, nullable=False)
    password=db.Column(db.String(200), nullable=False)


#load questions grouped by field
question_bank= {}
field_categories ={
    'Engineering & Technology':[
        'Computer Science', 'Information Technology','Electronics and Communication',
        'Electrical Engineering','Mechanical Engineering','Civil Engineering'
    ],
    'Core CS & IT Subjects': [
        'Data Structures', 'Operating Systems', 'Database Management System',
        'Computer Networks', 'Object Oriented Programming', 'Web Development',
        'Machine Learning', 'Artificial Intelligence', 'Software Engineering', 'Cyber Security'
    ],
    'Science Department': [
        'Mathematics', 'Physics', 'Chemistry', 'Statistics', 'Biotechnology'
    ],
    'Commerce & Management': [
        'Accounting', 'Finance', 'Marketing', 'Business Management', 'Economics'
    ],
    'Arts & Humanities': [
        'English Literature', 'History', 'Political Science', 'Psychology', 'Philosophy'
    ]
}

with open("questions.txt", "r") as file:
    for line in file:
        if "|" in line:
            field, q = line.strip().split("|", 1)
            field = field.strip()
            question_bank.setdefault(field, []).append(q.strip())

def generate_question_paper(selected_field, n_clusters=3, question_count=30):
    questions = question_bank.get(selected_field, [])
    if not questions:
        return []

    # Ensure we don't try to create more clusters than questions
    n_clusters = min(n_clusters, len(questions), question_count)
    
    if len(questions) <= question_count:
        # If we have fewer questions than requested, return all questions
        return random.sample(questions, min(len(questions), question_count))
    
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(questions)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(X)

    cluster_questions = [[] for _ in range(n_clusters)]
    for i, label in enumerate(kmeans.labels_):
        cluster_questions[label].append(questions[i])

    # Select questions from each cluster
    selected = []
    for qs in cluster_questions:
        if qs:
            selected.append(random.choice(qs))
    
    # If we need more questions, randomly select from remaining
    while len(selected) < question_count and len(questions) > len(selected):
        remaining = [q for q in questions if q not in selected]
        if remaining:
            selected.append(random.choice(remaining))
    
    return selected[:question_count]

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    fields = list(question_bank.keys())
    generated_questions = []
    selected_field = ""
    question_count = 5
    
    if request.method == "POST":
        selected_field = request.form.get("field")
        question_count = int(request.form.get("question_count", 5))
        generated_questions = generate_question_paper(selected_field, question_count=question_count)
        session["questions"] = generated_questions
        return redirect(url_for("paper"))
    
    return render_template("index.html", 
                         fields=fields, 
                         field_categories=field_categories,
                         questions=generated_questions,
                         selected_field=selected_field,
                         question_count=question_count)

@app.route("/paper")
def paper():
    if "questions" not in session:
        return redirect(url_for("index"))
    questions = session["questions"]
    return render_template("paper.html", questions=questions)

def cleanup_old_pdfs():
    """Remove PDF files older than 1 hour to prevent disk space issues"""
    static_dir = "static"
    if os.path.exists(static_dir):
        current_time = time.time()
        for pdf_file in glob.glob(os.path.join(static_dir, "*.pdf")):
            if os.path.getmtime(pdf_file) < current_time - 3600:  # 1 hour
                try:
                    os.remove(pdf_file)
                except:
                    pass

@app.route("/download")
def download():
    if "questions" not in session:
        return redirect(url_for("index"))
    
    # Clean up old PDFs before creating new one
    cleanup_old_pdfs()
    
    filepath = create_pdf(session["questions"])
    return send_file(filepath, as_attachment=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password. Please try again."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        existing_user = User.query.filter_by(username=request.form["username"]).first()
        if existing_user:
            error = "Username already exists. Please try a different one."
        else:
            hashed_pw = generate_password_hash(request.form["password"], method='pbkdf2:sha256')
            new_user = User(username=request.form["username"], password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("questions", None)
    return redirect(url_for("login"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET"])
def contact():
    return render_template("contact.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
