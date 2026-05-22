import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

# ======================
# APP INIT
# ======================
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'maisha_ai_secret_key_ultra_pro_2026'
)

# ======================
# DATABASE CONFIG (PRODUCTION SAFE)
# ======================
db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:PASSWORD_YAKO@localhost:5432/maishadb"
)

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# LOGIN MANAGER
# ======================
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ======================
# MODELS
# ======================
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)


class ChatHistory(db.Model):
    __tablename__ = "chat_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    sender = db.Column(db.String(10))  # user / ai
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ======================
# GROQ AI
# ======================
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
Wewe ni Maisha AI, mshauri wa vijana wa Afrika...
Jibu kwa Swanglish, mifano ya Tanzania, na majibu mafupi.
"""

# ======================
# ROUTES (AUTH)
# ======================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Username tayari ipo"

        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))

        return "Login failed"

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ======================
# HOME
# ======================
@app.route("/")
@login_required
def home():
    messages = ChatHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatHistory.timestamp.asc()).all()

    return render_template(
        "index.html",
        past_messages=messages,
        username=current_user.username
    )


@app.route("/new_chat")
@login_required
def new_chat():
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for("home"))

# ======================
# CHAT API
# ======================
@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.json
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "Andika message kwanza"})

    # save user msg
    user_msg = ChatHistory(
        user_id=current_user.id,
        sender="user",
        message=message
    )
    db.session.add(user_msg)
    db.session.commit()

    # history
    history = ChatHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatHistory.timestamp.desc()).limit(8).all()

    history.reverse()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for h in history:
        role = "user" if h.sender == "user" else "assistant"
        messages.append({"role": role, "content": h.message})

    # AI CALL
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )

        reply = res.choices[0].message.content

    except Exception as e:
        reply = "Error AI server: " + str(e)

    # save AI msg
    ai_msg = ChatHistory(
        user_id=current_user.id,
        sender="ai",
        message=reply
    )
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({"response": reply})

# ======================
# SHARE CHAT
# ======================
@app.route("/api/share_chat", methods=["POST"])
@login_required
def share_chat():
    chats = ChatHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatHistory.timestamp.asc()).all()

    text = "\n\n".join(
        f"{'WEWE' if c.sender=='user' else 'MAISHA AI'}: {c.message}"
        for c in chats
    )

    return jsonify({"chat": text})

# ======================
# SETTINGS API
# ======================
@app.route("/api/settings")
@login_required
def settings():
    return jsonify({
        "theme": "dark",
        "language": "sw"
    })

# ======================
# INIT DB + RUN
# ======================
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)