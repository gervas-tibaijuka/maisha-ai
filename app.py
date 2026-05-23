import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

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

# 4. ADVANCED DATABASE MODELS (Muundo Mpya wa ChatGPT-Style)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Mahusiano na conversations zake
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False, default='Mazungumzo Mapya')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Mahusiano na meseji zilizopo ndani yake
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat()
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
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
- Unaruhusiwa kutumia Markdown vizuri sana (**bold**, tables, bulleted lists, na code blocks zenye lugha husika).
"""

# 6. APP ROUTES (Mifumo ya Kurasa)
@app.route('/')
@login_required
def home():
    return render_template('index.html', username=current_user.username)

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


# 7. CONVERSATION MANAGEMENT API ENDPOINTS (ChatGPT Core Navigation)

@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    # Pakia orodha ya soga zote za mtumiaji kwa mpangilio wa mpya kwanza
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.created_at.desc()).all()
    return jsonify([c.to_dict() for c in conversations])

@app.route('/api/conversations/create', methods=['POST'])
@login_required
def create_conversation():
    data = request.json or {}
    title = data.get('title', 'Mazungumzo Mapya').strip()
    
    new_conv = Conversation(user_id=current_user.id, title=title[:50])
    db.session.add(new_conv)
    db.session.commit()
    return jsonify(new_conv.to_dict())

@app.route('/api/conversations/<int:conv_id>', methods=['GET'])
@login_required
def get_conversation_messages(conv_id):
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    # Pakia meseji zote zilizopo kwenye soga hii mahususi
    messages = ChatMessage.query.filter_by(conversation_id=conv.id).order_by(ChatMessage.timestamp.asc()).all()
    
    return jsonify({
        "conversation": conv.to_dict(),
        "messages": [{"sender": m.sender, "text": m.message} for m in messages]
    })

@app.route('/api/conversations/rename', methods=['POST'])
@login_required
def rename_conversation():
    data = request.json or {}
    conv_id = data.get('id')
    new_title = data.get('title', '').strip()
    
    if not conv_id or not new_title:
        return jsonify({"error": "Data hazijakamilika"}), 400
        
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    conv.title = new_title[:50]
    db.session.commit()
    return jsonify(conv.to_dict())

@app.route('/api/conversations/delete/<int:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/conversations/clear_all', methods=['POST'])
@login_required
def clear_all_conversations():
    Conversation.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})


# 8. REAL STREAMING ENGINE API (Server-Sent Events)

@app.route('/api/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    conv_id = data.get('conversation_id')
    
    if not user_message or not conv_id:
        return jsonify({"error": "Ujumbe au ID ya soga haijapatikana"}), 400

    # Hakikisha soga ni ya mtumiaji aliyelogin
    conv = Conversation.query.filter_by(id=conv_id, user_id=current_user.id).first_or_404()

    # 1. Hifadhi ujumbe wa mtumiaji kwenye DB mara moja
    user_msg_record = ChatMessage(conversation_id=conv.id, sender='user', message=user_message)
    db.session.add(user_msg_record)
    db.session.commit()

    # 2. Pakia kumbukumbu ya maongezi yaliyopita (Memory Context - Limit 10)
    history_records = ChatMessage.query.filter_by(conversation_id=conv.id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
    history_records.reverse()

    # 3. Jenga payload ya Groq API
    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    for record in history_records:
        role = "user" if record.sender == 'user' else "assistant"
        messages_payload.append({"role": role, "content": record.message})

    # Generator function inayotuma data kipande kwa kipande (Streaming Generator)
    def generate_stream_tokens():
        try:
            # Piga simu Groq ukiwasha mfumo wa streaming
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload,
                stream=True
            )
            
            ai_full_reply = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    ai_full_reply += token
                    yield token  # Tuma token moja kwa moja kwenda UI bila kupitia Event wrapper
            
            # Streaming ikimalizika kwa mafanikio, hifadhi jibu kamili la AI kwenye DB
            if ai_full_reply.strip():
                # Tunafungua app context mpya ndani ya thread kuhakikisha usalama wa DB session
                with app.app_context():
                    ai_msg_record = ChatMessage(conversation_id=conv.id, sender='ai', message=ai_full_reply)
                    db.session.add(ai_msg_record)
                    db.session.commit()

        except Exception as e:
            print(f"Streaming Engine Fault: {e}")
            yield f"\n[Hitilafu ya Kiufundi]: {str(e)}"

    # Rejesha token kama text stream safi inayosomeka moja kwa moja na JavaScript `reader.read()`
    return Response(generate_stream_tokens(), mimetype='text/plain')


# Inua majedwali mapya kiotomatiki kama yakikosekana
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)