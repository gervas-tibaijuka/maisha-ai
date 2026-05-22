import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from groq import Groq

app = Flask(__name__)

app.config['SECRET_KEY'] = 'maisha_ai_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maisha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------- MODELS ----------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    title = db.Column(db.String(200))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    sender = db.Column(db.String(10))
    message = db.Column(db.Text)

with app.app_context():
    db.create_all()

SYSTEM = """
Wewe ni Maisha AI, jibu kwa Swahili + English (Swanglish), fupi na practical.
"""

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template('index.html')


# GET all chats
@app.route('/api/chats')
def chats():
    all_chats = Chat.query.all()
    return jsonify({
        "chats":[
            {"id":c.id,"title":c.title} for c in all_chats
        ]
    })


# NEW chat
@app.route('/api/chat/new')
def new_chat():
    c = Chat(title="New Chat", user_id=1)
    db.session.add(c)
    db.session.commit()
    return jsonify({"id":c.id})


# GET messages
@app.route('/api/chat/<int:id>')
def get_chat(id):
    msgs = Message.query.filter_by(chat_id=id).all()
    return jsonify({
        "messages":[
            {"sender":m.sender,"message":m.message}
            for m in msgs
        ]
    })


# SEND message + AI
@app.route('/api/chat/send', methods=['POST'])
def send():
    data = request.json
    chat_id = data['chat_id']
    msg = data['message']

    # save user msg
    db.session.add(Message(chat_id=chat_id, sender='user', message=msg))
    db.session.commit()

    # history
    history = Message.query.filter_by(chat_id=chat_id).all()

    messages = [{"role":"system","content":SYSTEM}]
    for h in history:
        role = "user" if h.sender=="user" else "assistant"
        messages.append({"role":role,"content":h.message})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    reply = completion.choices[0].message.content

    db.session.add(Message(chat_id=chat_id, sender='ai', message=reply))
    db.session.commit()

    return jsonify({"response":reply})


if __name__ == '__main__':
    app.run(debug=True)