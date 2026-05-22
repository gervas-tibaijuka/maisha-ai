import os  # Hakikisha hii ipo juu kabisa ya app.py (Mstari wa kwanza)

from flask import Flask, render_template, request, jsonify, redirect, url_for
from groq import Groq
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'maisha_ai_secret_key_123'

# 1. Fetch the database URL from Render environment variables safely
db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:PASSWORD_YAKO@localhost:5432/maishadb")

# Render sometimes uses "postgres://", but SQLAlchemy requires "postgresql://"
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 2. Jedwali la Watumiaji (User Model)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# 3. JEDWALI JIPYA: Historia ya Chat (ChatHistory Model)
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # ama 'user' au 'ai'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Akili ya AI (Groq)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
SYSTEM_PROMPT = """
Wewe ni "Maisha AI", kocha wa kidijitali wa vijana wa Kitanzania na Afrika. 
Dira yako: “Kusaidia vijana wa Afrika kufanya maamuzi bora kwenye maisha ya kila siku.”
Ongea kwa Swanglish fupi ya kirafiki na ya mtaani yenye pointi zilizonyooka.
"""

# Routes za Authentication
@app.route('/')
@login_required
def home():
    # Wakati ukurasa unafunguka, pakia meseji zote za nyuma za mtumiaji huyu kutoka kwenye database
    past_messages = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.asc()).all()
    return render_template('index.html', username=current_user.username, past_messages=past_messages)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return "Mtumiaji huyu tayari yupo! Jaribu jina lingine."
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return '<div style="text-align:center; margin-top:100px;"><h2>Sajili Akaunti - Maisha AI</h2><form method="POST"><input type="text" name="username" placeholder="Username" required><br><br><input type="password" name="password" placeholder="Password" required><br><br><button type="submit">Sajili</button></form><p>Unayo akaunti? <a href="/login">Ingia</a></p></div>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        return "Jina au Password sio sahihi!"
    return '<div style="text-align:center; margin-top:100px;"><h2>Ingia - Maisha AI</h2><form method="POST"><input type="text" name="username" placeholder="Username" required><br><br><input type="password" name="password" placeholder="Password" required><br><br><button type="submit">Ingia</button></form><p>Huna akaunti? <a href="/signup">Sajili hapa</a></p></div>'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# API ya Chat yenye Kumbukumbu (Memory)
# API ya Chat yenye Kumbukumbu (Memory) iliyorekebishwa Indentation na Groq Syntax
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"response": "Tafadhali andika ujumbe wako..."})
        
    try:
        # 1. Hifadhi ujumbe wa mtumiaji kwenye PostgreSQL
        user_chat = ChatHistory(user_id=current_user.id, sender='user', message=user_message)
        db.session.add(user_chat)
        db.session.commit()
        
        # 2. Pakia meseji 6 za mwisho kama kumbukumbu (Memory)
        history_records = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(6).all()
        history_records.reverse()
        
        # Jenga mjumuisho wa meseji kwa ajili ya Groq API
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        for record in history_records:
            role = "user" if record.sender == 'user' else "assistant"
            messages_payload.append({"role": role, "content": record.message})
            
        # 3. Tuma data zote kwenda Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_payload
        )
        
        # HAPA NDIPO SULUHISHO: Groq inasoma hivi jibu lake
        ai_response = completion.choices[0].message.content
        
        # 4. Hifadhi jibu la AI kwenye PostgreSQL
        ai_chat = ChatHistory(user_id=current_user.id, sender='ai', message=ai_response)
        db.session.add(ai_chat)
        db.session.commit()
        
        return jsonify({"response": ai_response})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": f"Hitilafu: {e}"})

# Amri ya kutengeneza majedwali mapya ya database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
