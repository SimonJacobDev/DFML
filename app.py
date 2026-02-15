from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os, requests

AI_API_URL = "http://localhost:8000"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ================= DATABASE MODELS =================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    media_type = db.Column(db.String(10))  # image or video
    result = db.Column(db.String(20))      # real/fake/suspicious
    confidence = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class SocialPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    media_type = db.Column(db.String(10))
    result = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    report_file = db.Column(db.String(200))  # NEW
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def home():
    return render_template('index.html')  # Your homepage

# ================= AUTH ROUTES =================
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose another.", "error")
            return redirect(url_for('login'))

        # Hash password before storing
        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('social_feed'))
        else:
            flash("Invalid username or password", "error")

    return render_template("Login.html")



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ================= FEED =================
@app.route('/')
@login_required
def feed():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("feed.html", posts=posts)

# ================= UPLOAD =================
@app.route('/create-post', methods=['POST'])

def create_post():
    '''file = request.files['media']
    filename = secure_filename(file.filename)
    filepath = os.path.join('static/uploads', filename)
    file.save(filepath)

    media_type = "video" if filename.lower().endswith(('.mp4','.mov','.avi')) else "image"
    endpoint = "/predict_video" if media_type == "video" else "/predict_image"

    # Call AI server
    with open(filepath, 'rb') as f:
        res = requests.post(AI_API_URL + endpoint, files={'file': f})
    result = res.json()

    label = result['predicted_label']
    probs = result['mean_probabilities']
    confidence = max(probs['real'], probs['fake'])

    status = "real" if label == "real" else "fake"

    # Save in DB
    post = SocialPost(
        filename=filename,
        media_type=media_type,
        result=status,
        confidence=confidence,
        user_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()

    # Redirect to analysis page with result
    return redirect(url_for(
        'analysis1_result',
        filename=filename,
        result=status,
        confidence=round(confidence * 100, 2),
        media_type=media_type
    ))'''
    return render_template("analysis1.html")




# ================= REPORT =================
@app.route('/report-post/<int:post_id>')
@login_required
def report_post(post_id):
    flash("Post reported to moderation team.")
    return redirect(url_for('social_feed'))



@app.route('/social-feed')
def social_feed():
    posts = SocialPost.query.order_by(SocialPost.id.desc()).all()
    return render_template('social_feed.html', posts=posts)


@app.route('/analysis')
def analysis():
    return render_template("analysis.html")


@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")
if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # Create tables safely inside app context
    app.run(debug=True)
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)