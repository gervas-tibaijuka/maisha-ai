import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
from flask import jsonify

app = Flask(__name__)

# 1. USALAMA WA CRYPTOGRAPHY KEY
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'maisha_ai_secret_key_ultra_pro_2026')

# 2. SANIDI DATABASE YA POSTGRESQL (Mazingira ya Ndani na Mtandaoni kwa pg8000)
db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:PASSWORD_YAKO@localhost:5432/maishadb")

if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 3. MIFUMO YA USIMAMIZI WA LOGINS (FLASK-LOGIN)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 4. DATABASE MODELS (Majedwali ya Watumiaji na Maongezi)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' au 'ai'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 5. INJINI YA AI (GROQ CLIENT CONFIGURATION)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
Wewe ni "Maisha AI", kocha mahiri na mshauri wa karibu wa kidijitali kwa ajili ya vijana wa Kitanzania na Afrika nzima.
Dira yako kuu ni: “Kusaidia vijana wa Afrika kufanya maamuzi bora kwenye maisha ya kila siku.”

Unajibu maswali yanayohusu nyanja hizi kuu:
1. Life & Relationship Help (Ushauri wa maisha na mahusiano bila hukumu).
2. Education & Career Help (Mbinu za masomo, kuandika CV, stadi za kazi).
3. Money & Business Advice (Nidhamu ya fedha, akiba, uendeshaji wa biashara ndogo).
4. Realistic Motivation (Hamu thabiti ya ukweli inayochochea uwajibikaji).

Sheria za Majibu (ChatGPT Style):
- Ongea kwa lugha ya "Swanglish" ya mtaani inayovutia (Changanya Kiswahili na Kiingereza cha kawaida cha Dar es Salaam).
- Tumia mifano halisi ya Kitanzania (mfano: bando la simu, fremu mtaani, bodaboda, kupambana duka la nguo, daladala).
- Majibu yako yawe mafupi, yasiyo na maneno mengi yasiyo na tija, na yagawanywe kwa aya fupi au pointi ili yaonekane nadhifu kwenye screen.
"""

# 6. APP ROUTES (Mifumo ya Kurasa)
@app.route('/')
@login_required
def home():
    # Pakia historia kamili ya mtumiaji huyu kwa mpangilio sahihi wa muda
    past_messages = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.asc()).all()
    return render_template('index.html', username=current_user.username, past_messages=past_messages)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return '<div style="text-align:center; margin-top:100px;"><h3>Jina hili tayari lipo! <a href="/signup">Jaribu lingine</a></h3></div>'
            
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
        
    return '<div style="text-align:center; margin-top:100px; font-family:sans-serif;"><h2>Sajili Akaunti - Maisha AI</h2><br><form method="POST"><input type="text" name="username" placeholder="Jina la mtumiaji" style="padding:10px; width:250px;" required><br><br><input type="password" name="password" placeholder="Nenosiri" style="padding:10px; width:250px;" required><br><br><button type="submit" style="padding:10px 20px; background:#10a37f; color:white; border:none; border-radius:5px; cursor:pointer;">Sajili</button></form><p>Tayari una akaunti? <a href="/login">Ingia hapa</a></p></div>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        return '<div style="text-align:center; margin-top:100px;"><h3>Taarifa si sahihi! <a href="/login">Jaribu tena</a></h3></div>'
        
    return '<div style="text-align:center; margin-top:100px; font-family:sans-serif;"><h2>Ingia - Maisha AI</h2><br><form method="POST"><input type="text" name="username" placeholder="Jina la mtumiaji" style="padding:10px; width:250px;" required><br><br><input type="password" name="password" placeholder="Nenosiri" style="padding:10px; width:250px;" required><br><br><button type="submit" style="padding:10px 20px; background:#10a37f; color:white; border:none; border-radius:5px; cursor:pointer;">Ingia</button></form><p>Huna akaunti? <a href="/signup">Sajili hapa</a></p></div>'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/new_chat')
@login_required
def new_chat():
    # Kufuta historia ya sasa ya maongezi kuanza upya safi kabisa (ChatGPT style)
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('home'))

# 7. CHAT CORE API (Mfumo wenye Smart Context History-Memory)
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"response": "Tafadhali andika ujumbe wako..."})
        
    try:
        # Hifadhi ujumbe wa mteja kwanza kwenye PostgreSQL
        user_chat = ChatHistory(user_id=current_user.id, sender='user', message=user_message)
        db.session.add(user_chat)
        db.session.commit()
        
        # Pakia meseji 8 zilizopita ili kutengeneza kumbukumbu imara (AI Memory Context)
        history_records = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(8).all()
        history_records.reverse()
        
        # Jenga mjumuisho safi wa data za kutuma Groq
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        for record in history_records:
            role = "user" if record.sender == 'user' else "assistant"
            messages_payload.append({"role": role, "content": record.message})
            
        # Piga simu kwenda kwenye akili ya Llama 3.3 kupitia Groq API
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_payload
        )
        ai_response = completion.choices[0].message.content
        
        # Hifadhi jibu la AI ndani ya database ya PostgreSQL
        ai_chat = ChatHistory(user_id=current_user.id, sender='ai', message=ai_response)
        db.session.add(ai_chat)
        db.session.commit()
        
        return jsonify({"response": ai_response})
        
    except Exception as e:
        print(f"Server Core Error: {e}")
        return jsonify({"response": f"Samahani, kuna hitilafu ya kiufundi imetokea: {e}"})

# Tengeneza majedwali mapya ya mifumo kiotomatiki yakikosekana
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
