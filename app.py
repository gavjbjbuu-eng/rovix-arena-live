import os
import random
import time
from flask import Flask, jsonify, redirect, render_template_string, request, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "rovix_ultimate_live_arena_2026"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

USERS_FILE = "users.txt"
BETS_FILE = "bets.txt"
ROUND_STATE_FILE = "round_states.txt"
WIN_COUNT_FILE = "55x_wins.txt" 
HISTORY_FILE = "game_history.txt"
PROFILES_FILE = "creator_profiles.txt"
REELS_FILE = "reels.txt"
GIFTS_FILE = "gifts.txt"
WITHDRAWALS_FILE = "withdrawals.txt"
LIVE_STREAMS_FILE = "live_streams.txt"
RECHARGES_FILE = "recharges.txt"

ITEM_MULTIPLIERS = {
    "🍫": 5, "☕": 5, "🍿": 5, "🧋": 5,
    "🍦": 10, "🍕": 15, "🍔": 25, "🥤": 55
}

VALID_RECHARGE_PLANS = {
    99: 500,
    350: 1600,
    700: 4000,
    1500: 8000,
    3750: 20000,
    11500: 58000
}

def get_today_55x_wins():
    if not os.path.exists(WIN_COUNT_FILE): return 0
    with open(WIN_COUNT_FILE, "r") as f:
        content = f.read().strip().split("|")
        if len(content) == 2 and content[0] == time.strftime("%Y-%m-%d"):
            return int(content[1])
    return 0

def increment_55x_wins():
    today_str = time.strftime("%Y-%m-%d")
    current_wins = get_today_55x_wins()
    with open(WIN_COUNT_FILE, "w") as f:
        f.write(f"{today_str}|{current_wins + 1}\n")

def get_all_users():
    users = []
    if not os.path.exists(USERS_FILE): return users
    with open(USERS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 3:
                users.append({"phone": parts[0], "balance": int(parts[2])})
    return sorted(users, key=lambda x: x['balance'], reverse=True)

def get_user(phone):
    if not os.path.exists(USERS_FILE): return None
    with open(USERS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if parts[0] == phone: return {"phone": parts[0], "password": parts[1], "balance": int(parts[2])}
    return None

def update_user_balance(phone, new_balance):
    lines = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if parts[0] == phone: lines.append(f"{parts[0]}|{parts[1]}|{new_balance}\n")
                else: lines.append(line)
        with open(USERS_FILE, "w") as f: f.writelines(lines)

def get_creator_profile(phone):
    profile = {"bio": "Exploring the Creator Arena ✨", "insta": "#", "youtube": "#", "pic": "https://i.imgur.com/6VBx3io.png"}
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 5 and parts[0] == phone:
                    profile = {"bio": parts[1], "insta": parts[2], "youtube": parts[3], "pic": parts[4]}
    return profile

def update_creator_profile(phone, bio, insta, youtube, pic):
    profiles = {}
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 5:
                    profiles[parts[0]] = parts[1:]
    profiles[phone] = [bio, insta, youtube, pic]
    with open(PROFILES_FILE, "w") as f:
        for p, d in profiles.items():
            f.write(f"{p}|{'|'.join(d)}\n")

def get_creator_cheers(phone):
    total_cheers = 0
    if os.path.exists(GIFTS_FILE):
        with open(GIFTS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3 and parts[1] == phone:
                    try:
                        total_cheers += int(parts[2])
                    except:
                        pass
    return total_cheers

def get_today_withdrawals(phone):
    total_withdrawn = 0
    today = time.strftime("%Y-%m-%d")
    if os.path.exists(WITHDRAWALS_FILE):
        with open(WITHDRAWALS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3 and parts[0] == phone and parts[1].startswith(today):
                    total_withdrawn += float(parts[2])
    return total_withdrawn

def record_bet(phone, round_id, item, amount):
    lines = []
    bet_updated = False
    if os.path.exists(BETS_FILE):
        with open(BETS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 4 and parts[0] == phone and int(parts[1]) == round_id and parts[2] == item:
                    current_amt = int(parts[3]) + amount
                    if current_amt > 0:
                        lines.append(f"{phone}|{round_id}|{item}|{current_amt}\n")
                    bet_updated = True
                else:
                    lines.append(line)
    if not bet_updated and amount > 0:
        lines.append(f"{phone}|{round_id}|{item}|{amount}\n")
    with open(BETS_FILE, "w") as f:
        f.writelines(lines)

def get_user_bets(phone, round_id):
    user_bets = {}
    if not os.path.exists(BETS_FILE): return user_bets
    with open(BETS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) == 4 and parts[0] == phone and int(parts[1]) == round_id:
                user_bets[parts[2]] = int(parts[3])
    return user_bets

def get_round_total_bets(round_id):
    item_totals = {item: 0 for item in ITEM_MULTIPLIERS.keys()}
    if not os.path.exists(BETS_FILE): return item_totals
    with open(BETS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) == 4 and int(parts[1]) == round_id:
                it, amt = parts[2], int(parts[3])
                if it in item_totals:
                    item_totals[it] += amt
    return item_totals

def add_to_history(round_id, winning_item):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = [line.strip() for line in f.readlines() if line.strip()]
    entry = f"{round_id}:{winning_item}"
    if entry not in history:
        history.append(entry)
        if len(history) > 10: history = history[-10:]
        with open(HISTORY_FILE, "w") as f:
            f.write("\n".join(history) + "\n")

def get_game_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    history_list = []
    for line in lines:
        parts = line.split(":")
        if len(parts) == 2:
            history_list.append({"round_id": parts[0], "item": parts[1]})
    return history_list[-10:]

def determine_admin_profit_winning_item(round_id):
    if os.path.exists(ROUND_STATE_FILE):
        with open(ROUND_STATE_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 2 and int(parts[0]) == round_id:
                    winning_item = parts[1]
                    add_to_history(round_id, winning_item)
                    return winning_item

    item_totals = get_round_total_bets(round_id)
    total_collection = sum(item_totals.values())
    items = list(ITEM_MULTIPLIERS.keys())
    
    if total_collection == 0:
        random.seed(round_id)
        winning_item = random.choice(items)
    else:
        results_analysis = []
        for item, mult in ITEM_MULTIPLIERS.items():
            payout = item_totals[item] * mult
            admin_profit = total_collection - payout
            results_analysis.append({"item": item, "profit": admin_profit})

        profitable_items = [r for r in results_analysis if r['profit'] > 0]
        soda_data = next((r for r in results_analysis if r['item'] == "🥤"), None)
        can_trigger_55x = (get_today_55x_wins() < 3) and soda_data and (soda_data['profit'] > 0)

        if can_trigger_55x and random.random() < 0.25:
            winning_item = "🥤"
            increment_55x_wins()
        elif profitable_items:
            profitable_items.sort(key=lambda x: x['profit'], reverse=True)
            winning_item = profitable_items[0]['item']
        else:
            results_analysis.sort(key=lambda x: x['profit'], reverse=True)
            winning_item = results_analysis[0]['item']

    with open(ROUND_STATE_FILE, "a") as f:
        f.write(f"{round_id}|{winning_item}\n")
    add_to_history(round_id, winning_item)
    return winning_item

@app.route('/')
def splash():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROVIX ARENA</title>
        <style>
            body { background: #05070a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif; overflow: hidden; }
            .splash-box { text-align: center; animation: zoomIn 1.5s ease-out; }
            .logo-icon { font-size: 75px; background: linear-gradient(135deg, #38bdf8, #a855f7, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 40px rgba(56,189,248,0.6); margin-bottom: 15px; }
            .logo-text { font-size: 42px; font-weight: 900; letter-spacing: 2px; background: linear-gradient(45deg, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .tagline { color: #94a3b8; font-size: 13px; margin-top: 10px; letter-spacing: 1px; text-transform: uppercase; }
            @keyframes zoomIn { 0% { transform: scale(0.7); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        </style>
        <script>
            setTimeout(() => { window.location.href = "/check_auth"; }, 2500);
        </script>
    </head>
    <body>
        <div class="splash-box">
            <div class="logo-icon">⚡👑</div>
            <div class="logo-text">ROVIX ARENA</div>
            <div class="tagline">Ultimate Creator & Live Hub</div>
        </div>
    </body>
    </html>
    """)

@app.route('/check_auth')
def check_auth():
    if 'phone' in session: return redirect('/feed')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        phone = request.form.get('phone').strip()
        password = request.form.get('password').strip()
        action = request.form.get('action')
        
        if not phone or not password:
            error = "Phone and Password cannot be empty!"
        elif action == 'register':
            if get_user(phone):
                error = "Unique Username / Phone already registered!"
            else:
                lines = []
                if os.path.exists(USERS_FILE):
                    with open(USERS_FILE, "r") as f: lines = f.readlines()
                lines.append(f"{phone}|{password}|50\n")
                with open(USERS_FILE, "w") as f: f.writelines(lines)
                session['phone'] = phone
                return redirect('/feed')
        else:
            user = get_user(phone)
            if user and user['password'] == password:
                session['phone'] = phone
                return redirect('/feed')
            else:
                error = "Invalid credentials!"
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROVIX - Login</title>
        <style>
            body { background: #07090e; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif; }
            .auth-card { background: #111827; padding: 30px; border-radius: 16px; width: 90%; max-width: 400px; text-align: center; box-shadow: 0 0 25px rgba(56, 189, 248, 0.2); border: 1px solid #1e293b; }
            .logo { font-size: 32px; font-weight: 900; background: linear-gradient(45deg, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
            input { width: 100%; padding: 12px; margin: 10px 0; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 8px; font-size: 16px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; margin-top: 10px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
            .btn-login { background: linear-gradient(135deg, #10b981, #059669); color: white; }
            .btn-reg { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }
        </style>
    </head>
    <body>
        <div class="auth-card">
            <div class="logo">⚡ ROVIX ARENA</div>
            {% if error %}<p style="color:#ef4444; font-size:14px;">{{error}}</p>{% endif %}
            <form method="POST">
                <input type="text" name="phone" placeholder="📱 Unique Username / Phone" required>
                <input type="password" name="password" placeholder="🔑 Password" required>
                <button type="submit" name="action" value="login" class="btn-login">Login</button>
                <button type="submit" name="action" value="register" class="btn-reg">Register Unique ID (+50 Bonus)</button>
            </form>
        </div>
    </body>
    </html>
    """, error=error)

@app.route('/logout')
def logout():
    session.pop('phone', None)
    return redirect('/')

@app.route('/feed')
def feed():
    if 'phone' not in session: return redirect('/login')
    
    reels = []
    if os.path.exists(REELS_FILE):
        with open(REELS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    reels.append({"phone": parts[0], "url": parts[1], "cap": parts[2]})

    active_lives = []
    if os.path.exists(LIVE_STREAMS_FILE):
        with open(LIVE_STREAMS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 2 and parts[1] == 'active':
                    active_lives.append(parts[0])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rovix - Feed & Live</title>
        <style>
            body { background: #000; color: white; margin: 0; font-family: sans-serif; overflow: hidden; }
            .feed-container { height: calc(100vh - 60px); overflow-y: scroll; scroll-snap-type: y mandatory; -webkit-overflow-scrolling: touch; }
            .reel { height: 100%; width: 100%; scroll-snap-align: start; scroll-snap-stop: always; position: relative; display: flex; justify-content: center; align-items: center; background: #111; }
            .nav-bottom { position: fixed; bottom: 0; width: 100%; height: 60px; background: #0f172a; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #1e293b; z-index: 100; }
            .nav-item { color: #94a3b8; text-decoration: none; font-size: 13px; font-weight: bold; display: flex; flex-direction: column; align-items: center; }
            .nav-item.active { color: #38bdf8; }
            .overlay { position: absolute; bottom: 80px; left: 15px; text-align: left; z-index: 10; right: 80px; }
            .gift-panel { position: absolute; right: 15px; bottom: 100px; display: flex; flex-direction: column; gap: 10px; z-index: 20; }
            .gift-btn { background: rgba(15,23,42,0.85); border: 1px solid #38bdf8; border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; font-size: 22px; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            .sound-btn { position: absolute; top: 20px; right: 20px; background: rgba(0,0,0,0.6); color: white; border: 1px solid #38bdf8; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; cursor: pointer; z-index: 30; backdrop-filter: blur(4px); }
            .live-banner { position: absolute; top: 20px; left: 15px; background: #ef4444; color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; text-decoration: none; display: flex; align-items: center; gap: 6px; z-index: 30; box-shadow: 0 0 15px rgba(239,68,68,0.8); animation: pulseLive 1.5s infinite; }
            @keyframes pulseLive { 0% { transform: scale(1); } 50% { transform: scale(1.03); } 100% { transform: scale(1); } }
            .search-bar-top { position: absolute; top: 20px; right: 135px; z-index: 30; display: flex; gap: 5px; }
            .search-bar-top input { padding: 6px 12px; border-radius: 20px; border: 1px solid #38bdf8; background: rgba(0,0,0,0.7); color: white; font-size: 12px; outline: none; width: 110px; }
            .search-bar-top button { padding: 6px 12px; border-radius: 20px; border: none; background: #38bdf8; color: black; font-weight: bold; cursor: pointer; font-size: 12px; }
        </style>
    </head>
    <body>
        {% if active_lives %}
        <a href="/live/{{active_lives[0]}}" class="live-banner">🔴 @{{active_lives[0]}} is LIVE! Join Hub</a>
        {% endif %}

        <div class="search-bar-top">
            <input type="text" id="searchUserInput" placeholder="Search ID...">
            <button onclick="searchUser()">🔍</button>
        </div>

        <div class="feed-container" id="feedContainer">
            {% if reels|length == 0 %}
            <div class="reel" style="flex-direction: column; color: #94a3b8; text-align: center; padding: 20px;">
                <h2>🎬 No Reels Yet!</h2>
                <p style="font-size: 14px;">Go to your profile and upload your first reel video.</p>
                <a href="/profile/{{session['phone']}}" style="margin-top: 15px; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold;">Upload Reel</a>
            </div>
            {% else %}
                {% for r in reels %}
                <div class="reel">
                    <video class="reel-video" src="{{r.url}}" autoplay loop playsinline muted style="width:100%; height:100%; object-fit:cover;"></video>
                    <button class="sound-btn" onclick="toggleSound(this)">🔇 Unmute</button>
                    <div class="overlay">
                        <h3 style="margin:0 0 5px 0;"><a href="/profile/{{r.phone}}" style="color:#38bdf8; text-decoration:none; text-shadow:0 2px 4px rgba(0,0,0,0.9);">@{{r.phone}}</a></h3>
                        <p style="margin:0; font-size:14px; text-shadow: 0 2px 4px rgba(0,0,0,0.9); word-break: break-word;">{{r.cap}}</p>
                    </div>
                    {% if r.phone != session['phone'] %}
                    <div class="gift-panel">
                        <button class="gift-btn" onclick="sendGift('{{r.phone}}', 10)" title="Gift 10 Cheers">🎁</button>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            {% endif %}
        </div>

        <div class="nav-bottom">
            <a href="/feed" class="nav-item active">🏠 Feed</a>
            <a href="/live_feed" class="nav-item">🔴 Live</a>
            <a href="/game" class="nav-item">🎮 Play Game</a>
            <a href="/profile/{{session['phone']}}" class="nav-item">👤 Profile</a>
        </div>

        <script>
            function searchUser() {
                let query = document.getElementById('searchUserInput').value.trim();
                if(query) { window.location.href = '/profile/' + encodeURIComponent(query); }
            }

            function toggleSound(btn) {
                let currentReel = btn.closest('.reel');
                let video = currentReel.querySelector('video');
                if(video.muted) {
                    video.muted = false;
                    btn.innerText = "🔊 Mute";
                } else {
                    video.muted = true;
                    btn.innerText = "🔇 Unmute";
                }
            }

            function sendGift(creatorPhone, amount) {
                fetch('/gift_creator', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ creator_phone: creatorPhone, amount: amount })
                }).then(res => res.json()).then(data => {
                    if(data.success) {
                        alert("🎁 Gifted " + amount + " Cheers successfully!");
                    } else {
                        alert("❌ " + data.error);
                    }
                });
            }
        </script>
    </body>
    </html>
    """, reels=reels, active_lives=active_lives)

@app.route('/live_feed')
def live_feed():
    if 'phone' not in session: return redirect('/login')
    active_lives = []
    if os.path.exists(LIVE_STREAMS_FILE):
        with open(LIVE_STREAMS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 2 and parts[1] == 'active':
                    active_lives.append(parts[0])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rovix - Live Feeds Hub</title>
        <style>
            body { background: #000; color: white; margin: 0; font-family: sans-serif; overflow: hidden; }
            .feed-container { height: calc(100vh - 60px); overflow-y: scroll; scroll-snap-type: y mandatory; -webkit-overflow-scrolling: touch; }
            .live-card { height: 100%; width: 100%; scroll-snap-align: start; scroll-snap-stop: always; position: relative; display: flex; justify-content: center; align-items: center; background: #111; flex-direction: column; text-align: center; }
            .nav-bottom { position: fixed; bottom: 0; width: 100%; height: 60px; background: #0f172a; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #1e293b; z-index: 100; }
            .nav-item { color: #94a3b8; text-decoration: none; font-size: 13px; font-weight: bold; display: flex; flex-direction: column; align-items: center; }
            .nav-item.active { color: #38bdf8; }
            .live-badge { background: #ef4444; color: white; padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; animation: pulseLive 1.5s infinite; margin-bottom: 15px; }
            @keyframes pulseLive { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
            .join-btn { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 15px; box-shadow: 0 4px 15px rgba(59,130,246,0.5); }
        </style>
    </head>
    <body>
        <div class="feed-container">
            {% if active_lives|length == 0 %}
            <div class="live-card" style="padding: 20px; color: #94a3b8;">
                <div style="font-size: 50px; margin-bottom: 10px;">🔴😴</div>
                <h2>No Active Live Streams Right Now!</h2>
                <p style="font-size: 14px;">Go to your profile and click 'Start Live Stream Studio' to go live.</p>
                <a href="/profile/{{session['phone']}}" style="margin-top: 15px; background: #ef4444; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold;">Start Live</a>
            </div>
            {% else %}
                {% for creator in active_lives %}
                <div class="live-card">
                    <div style="font-size: 65px; margin-bottom: 10px;">🎥🔴</div>
                    <div class="live-badge">🔴 LIVE STREAM BROADCAST</div>
                    <h2 style="color: #38bdf8; margin: 5px 0 20px 0; font-size: 26px;">@{{creator}}</h2>
                    <a href="/live/{{creator}}" class="join-btn">🚀 Join Live Stream Room</a>
                </div>
                {% endfor %}
            {% endif %}
        </div>

        <div class="nav-bottom">
            <a href="/feed" class="nav-item">🏠 Feed</a>
            <a href="/live_feed" class="nav-item active">🔴 Live</a>
            <a href="/game" class="nav-item">🎮 Play Game</a>
            <a href="/profile/{{session['phone']}}" class="nav-item">👤 Profile</a>
        </div>
    </body>
    </html>
    """, active_lives=active_lives)

@app.route('/start_live', methods=['POST'])
def start_live():
    if 'phone' not in session: return jsonify({'success': False})
    phone = session['phone']
    with open(LIVE_STREAMS_FILE, "w") as f:
        f.write(f"{phone}|active|{time.time()}\n")
    return jsonify({'success': True})

@app.route('/stop_live', methods=['POST'])
def stop_live():
    if 'phone' not in session: return jsonify({'success': False})
    if os.path.exists(LIVE_STREAMS_FILE):
        os.remove(LIVE_STREAMS_FILE)
    return jsonify({'success': True})

@app.route('/live/<phone>')
def live_stream(phone):
    if 'phone' not in session: return redirect('/login')
    prof = get_creator_profile(phone)
    cheers_received = get_creator_cheers(phone)
    is_creator = (session['phone'] == phone)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live - @{{phone}}</title>
        <style>
            body { background: #07090e; color: white; margin: 0; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: space-between; height: 100vh; overflow: hidden; }
            .live-container { width: 100%; height: 100%; position: relative; display: flex; flex-direction: column; justify-content: flex-end; background: #000; }
            
            video { width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; z-index: 1; transform: scaleX(-1); }
            canvas { width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; z-index: 1; display: none; }
            
            .f-cyberpunk { filter: contrast(1.5) saturate(2.2) hue-rotate(310deg) drop-shadow(0 0 20px #00ffff); }
            .f-hollywood { filter: contrast(1.2) brightness(1.1) sepia(0.2) saturate(1.4) drop-shadow(0 0 10px rgba(255,215,0,0.5)); }
            .f-dreamyaura { filter: blur(0.3px) brightness(1.25) saturate(1.6) contrast(0.95) drop-shadow(0 0 25px #ff69b4); }
            .f-goldenhour { filter: sepia(0.5) saturate(1.8) contrast(1.1) brightness(1.05) hue-rotate(-15deg); }
            .f-matrix      { filter: contrast(1.8) saturate(2.0) hue-rotate(90deg) brightness(1.05); }
            .f-iceblue     { filter: contrast(1.3) saturate(1.6) hue-rotate(180deg) brightness(1.15); }
            .f-velvetnoir  { filter: grayscale(1) contrast(1.6) brightness(0.9); }

            .creator-box { position: absolute; top: 15px; left: 15px; display: flex; align-items: center; gap: 10px; background: rgba(0,0,0,0.65); padding: 6px 12px; border-radius: 30px; border: 1px solid #38bdf8; z-index: 10; backdrop-filter: blur(6px); }
            .avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
            .live-tag { background: #ef4444; color: white; font-size: 9px; padding: 2px 6px; border-radius: 10px; font-weight: bold; animation: pulse 1s infinite; }
            @keyframes pulse { 0% { opacity: 0.6; } 100% { opacity: 1; } }
            
            .chat-box { width: 100%; max-height: 160px; overflow-y: auto; padding: 10px 15px; display: flex; flex-direction: column; gap: 6px; box-sizing: border-box; position: relative; z-index: 10; margin-bottom: 60px; scrollbar-width: none; }
            .chat-box::-webkit-scrollbar { display: none; }
            .chat-msg { background: rgba(15,23,42,0.75); padding: 6px 10px; border-radius: 8px; font-size: 13px; max-width: 85%; border-left: 3px solid #38bdf8; backdrop-filter: blur(5px); word-break: break-word; }
            
            .filter-tray { position: absolute; top: 70px; left: 15px; display: flex; gap: 8px; z-index: 10; overflow-x: auto; width: calc(100% - 30px); padding-bottom: 5px; scrollbar-width: none; }
            .filter-tray::-webkit-scrollbar { display: none; }
            .f-btn { background: rgba(15,23,42,0.85); border: 1px solid #38bdf8; color: white; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; cursor: pointer; backdrop-filter: blur(6px); white-space: nowrap; box-shadow: 0 0 8px rgba(56,189,248,0.3); }

            .control-bar { position: absolute; bottom: 0; padding: 10px 15px; background: rgba(15,23,42,0.95); display: flex; gap: 8px; width: 100%; box-sizing: border-box; border-top: 1px solid #1e293b; z-index: 10; backdrop-filter: blur(10px); align-items: center; }
            input { flex-grow: 1; padding: 10px; background: #1e293b; border: 1px solid #334155; color: white; border-radius: 8px; outline: none; font-size: 14px; }
            
            .gift-panel-live { position: absolute; bottom: 65px; width: 100%; display: flex; gap: 6px; padding: 6px 15px; justify-content: center; z-index: 10; background: linear-gradient(to top, rgba(7,9,14,0.95), transparent); flex-wrap: wrap; box-sizing: border-box; }
            .g-btn { background: rgba(30,41,59,0.9); color: #38bdf8; border: 1px solid #38bdf8; padding: 6px 12px; border-radius: 20px; font-weight: bold; cursor: pointer; font-size: 11px; backdrop-filter: blur(8px); box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: flex; align-items: center; gap: 4px; }
            
            .cam-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: #07090e; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 50; padding: 20px; text-align: center; }
            .unflipped-text { position: absolute; z-index: 15; width: 100%; text-align: center; top: 50%; transform: translateY(-50%); pointer-events: none; }
        </style>
    </head>
    <body>
        <div id="camOverlay" class="cam-overlay">
            <div style="font-size: 50px; margin-bottom: 10px;">⚡📸</div>
            <h2 style="color:#38bdf8; margin-bottom:5px;">Connecting Studio...</h2>
            <p style="color:#94a3b8; font-size:12px;">Please grant camera & mic permissions</p>
        </div>

        <div class="live-container">
            <video id="liveVideo" autoplay playsinline muted></video>
            <canvas id="liveCanvas"></canvas>

            <div id="simulatorText" class="unflipped-text" style="display:none;">
                <div style="font-size: 20px; font-weight: bold; color: #38bdf8; text-shadow: 0 2px 8px rgba(0,0,0,0.9);">⚡ ROVIX STUDIO ⚡</div>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 5px; text-shadow: 0 2px 6px rgba(0,0,0,0.9);">@{{phone}} Live Broadcast</div>
            </div>

            <div class="creator-box">
                <img src="{{prof.pic}}" class="avatar">
                <div>
                    <div style="font-weight: bold; font-size: 13px; color:#38bdf8;">@{{phone}}</div>
                    <div class="live-tag">LIVE</div>
                </div>
            </div>

            <div class="filter-tray">
                <button class="f-btn" onclick="setFilter('')">✨ Standard</button>
                <button class="f-btn" onclick="setFilter('f-cyberpunk')" style="border-color:#00ffff; color:#00ffff;">⚡ Cyberpunk</button>
                <button class="f-btn" onclick="setFilter('f-hollywood')" style="border-color:#ffd700; color:#ffd700;">🌟 Hollywood</button>
                <button class="f-btn" onclick="setFilter('f-dreamyaura')" style="border-color:#ff69b4; color:#ff69b4;">💖 Dreamy</button>
                <button class="f-btn" onclick="setFilter('f-goldenhour')" style="border-color:#ffa500; color:#ffa500;">🌅 Golden</button>
                <button class="f-btn" onclick="setFilter('f-matrix')" style="border-color:#00ff00; color:#00ff00;">🟢 Matrix</button>
                <button class="f-btn" onclick="setFilter('f-iceblue')" style="border-color:#38bdf8; color:#38bdf8;">❄️ Ice Blue</button>
                <button class="f-btn" onclick="setFilter('f-velvetnoir')" style="border-color:#ffffff; color:#ffffff;">🎞️ Noir</button>
            </div>

            <div style="position: absolute; top: 20px; right: 15px; background: rgba(0,0,0,0.75); padding: 6px 12px; border-radius: 20px; border: 1px solid #10b981; font-size: 12px; z-index:10; backdrop-filter: blur(5px);">
                🎁 <strong style="color: #10b981;" id="cheersDisplay">{{cheers_received}}</strong>
            </div>

            <div class="chat-box" id="chatBox">
                <div class="chat-msg">👋 Welcome to @{{phone}}'s Live Stream!</div>
            </div>

            <div class="gift-panel-live">
                {% if not is_creator %}
                <button class="g-btn" onclick="sendLiveGift(10)">🍫 10</button>
                <button class="g-btn" onclick="sendLiveGift(50)">☕ 50</button>
                <button class="g-btn" onclick="sendLiveGift(100)">🎁 100</button>
                {% else %}
                <button class="g-btn" id="camToggleBtn" onclick="toggleCamera()" style="background:#f59e0b; color:#000;">📹 Cam Off</button>
                <button class="g-btn" id="micToggleBtn" onclick="toggleMic()" style="background:#3b82f6; color:#fff;">🎤 Mute</button>
                <button class="g-btn" onclick="endLive()" style="background:#ef4444; color:#fff;">🔴 End</button>
                {% endif %}
            </div>

            <div class="control-bar">
                <input type="text" id="msgInput" placeholder="Say something...">
                <button onclick="sendComment()" style="background:#3b82f6; color:white; border:none; padding:10px 16px; border-radius:8px; font-weight:bold; cursor:pointer;">Send</button>
            </div>
        </div>

        <script>
            let localStream = null;
            const videoElem = document.getElementById('liveVideo');
            const canvasElem = document.getElementById('liveCanvas');
            const ctx = canvasElem.getContext('2d');
            let isCamActive = true;
            let isMicActive = true;

            window.addEventListener('DOMContentLoaded', () => { startCamera(); });

            async function startCamera() {
                try {
                    localStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: true });
                    videoElem.srcObject = localStream;
                    document.getElementById('camOverlay').style.display = 'none';
                    document.getElementById('simulatorText').style.display = 'none';
                    videoElem.style.display = 'block';
                    canvasElem.style.display = 'none';
                } catch (e) {
                    activateStudioSimulator();
                }
            }

            function activateStudioSimulator() {
                document.getElementById('camOverlay').style.display = 'none';
                videoElem.style.display = 'none';
                canvasElem.style.display = 'block';
                document.getElementById('simulatorText').style.display = 'block';
                let hue = 0;
                function drawStudio() {
                    ctx.fillStyle = "#07090e";
                    ctx.fillRect(0, 0, canvasElem.width, canvasElem.height);
                    ctx.beginPath();
                    ctx.arc(canvasElem.width / 2 + Math.sin(Date.now() / 1000) * 80, canvasElem.height / 2 + Math.cos(Date.now() / 1000) * 60, 120, 0, Math.PI * 2);
                    ctx.fillStyle = `hsla(${hue}, 80%, 50%, 0.25)`;
                    ctx.fill();
                    hue = (hue + 1) % 360;
                    requestAnimationFrame(drawStudio);
                }
                canvasElem.width = window.innerWidth;
                canvasElem.height = window.innerHeight;
                drawStudio();
            }

            function toggleCamera() {
                if(!localStream) return;
                let tracks = localStream.getVideoTracks();
                if(tracks.length > 0) {
                    isCamActive = !isCamActive;
                    tracks[0].enabled = isCamActive;
                    document.getElementById('camToggleBtn').innerText = isCamActive ? "📹 Cam Off" : "📸 Cam On";
                }
            }

            function toggleMic() {
                if(!localStream) return;
                let tracks = localStream.getAudioTracks();
                if(tracks.length > 0) {
                    isMicActive = !isMicActive;
                    tracks[0].enabled = isMicActive;
                    document.getElementById('micToggleBtn').innerText = isMicActive ? "🎤 Mute" : "🔊 Unmute";
                }
            }

            function setFilter(className) {
                videoElem.className = className;
                canvasElem.className = className;
            }

            function sendLiveGift(amount) {
                fetch('/gift_creator', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ creator_phone: '{{phone}}', amount: amount })
                }).then(res => res.json()).then(data => {
                    if(data.success) {
                        let chat = document.getElementById('chatBox');
                        chat.innerHTML += `<div class="chat-msg" style="border-color:#10b981; color:#10b981;">🎁 Gifted ${amount} Cheers!</div>`;
                        chat.scrollTop = chat.scrollHeight;
                        let cDisp = document.getElementById('cheersDisplay');
                        cDisp.innerText = parseInt(cDisp.innerText) + amount;
                    } else { alert("❌ " + data.error); }
                });
            }

            function sendComment() {
                let input = document.getElementById('msgInput');
                if(input.value.trim() === '') return;
                let chat = document.getElementById('chatBox');
                chat.innerHTML += `<div class="chat-msg"><b>@{{session['phone']}}:</b> ${input.value}</div>`;
                input.value = '';
                chat.scrollTop = chat.scrollHeight;
            }

            function endLive() {
                if(localStream) { localStream.getTracks().forEach(t => t.stop()); }
                fetch('/stop_live', { method: 'POST' }).then(() => { window.location.href = '/feed'; });
            }
        </script>
    </body>
    </html>
    """, phone=phone, prof=prof, cheers_received=cheers_received, is_creator=is_creator)

@app.route('/gift_creator', methods=['POST'])
def gift_creator():
    if 'phone' not in session: return jsonify({'success': False, 'error': 'Unauthorized'})
    data = request.get_json()
    creator_phone = data.get('creator_phone')
    amount = int(data.get('amount', 0))
    sender_phone = session['phone']
    if sender_phone == creator_phone: return jsonify({'success': False, 'error': 'Cannot gift yourself!'})
    user = get_user(sender_phone)
    if user['balance'] < amount: return jsonify({'success': False, 'error': 'Not enough balance!'})
    update_user_balance(sender_phone, user['balance'] - amount)
    with open(GIFTS_FILE, "a") as f:
        f.write(f"{sender_phone}|{creator_phone}|{amount}|{time.time()}\n")
    return jsonify({'success': True})

@app.route('/recharge', methods=['POST'])
def recharge():
    if 'phone' not in session: return jsonify({'success': False, 'error': 'Unauthorized'})
    data = request.get_json()
    try: amount = int(data.get('amount', 0))
    except: return jsonify({'success': False, 'error': 'Invalid amount!'})
    utr = data.get('utr', '').strip()
    if amount not in VALID_RECHARGE_PLANS: return jsonify({'success': False, 'error': 'Invalid plan!'})
    if not utr or len(utr) < 6: return jsonify({'success': False, 'error': 'Enter valid UTR ID!'})
    phone = session['phone']
    cheers_to_add = VALID_RECHARGE_PLANS[amount]
    with open(RECHARGES_FILE, "a") as f:
        f.write(f"{phone}|{amount}|{cheers_to_add}|{utr}|{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    user = get_user(phone)
    if user:
        new_balance = user['balance'] + cheers_to_add
        update_user_balance(phone, new_balance)
        return jsonify({'success': True, 'new_balance': new_balance})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'phone' not in session: return jsonify({'success': False, 'error': 'Unauthorized'})
    data = request.get_json()
    rupees_requested = float(data.get('rupees', 0))
    phone = session['phone']
    total_cheers = get_creator_cheers(phone)
    total_ice = total_cheers / 4.0 
    max_rupees = total_ice / 2.0   
    if rupees_requested < 200: return jsonify({'success': False, 'error': 'Minimum withdrawal is ₹200'})
    if rupees_requested > max_rupees: return jsonify({'success': False, 'error': 'Insufficient earnings'})
    if get_today_withdrawals(phone) + rupees_requested > 10000: return jsonify({'success': False, 'error': 'Daily limit ₹10,000'})
    cheers_to_deduct = int(rupees_requested * 8)
    with open(WITHDRAWALS_FILE, "a") as f:
        f.write(f"{phone}|{time.strftime('%Y-%m-%d %H:%M:%S')}|{rupees_requested}|{cheers_to_deduct}\n")
    with open(GIFTS_FILE, "a") as f:
        f.write(f"WITHDRAW|{phone}|-{cheers_to_deduct}|{time.time()}\n")
    return jsonify({'success': True, 'message': f'Withdrawn ₹{rupees_requested} successfully!'})

@app.route('/profile/<phone>', methods=['GET', 'POST'])
def profile(phone):
    if 'phone' not in session: return redirect('/login')
    target_user = get_user(phone)
    if not target_user: return "User not found", 404
    prof = get_creator_profile(phone)
    msg = ""
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile' and session['phone'] == phone:
            bio = request.form.get('bio')
            insta = request.form.get('insta')
            youtube = request.form.get('youtube')
            pic_url = prof['pic']
            if 'pic_file' in request.files:
                file = request.files['pic_file']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"profile_{phone}_{int(time.time())}_{filename}")
                    file.save(filepath)
                    pic_url = '/' + filepath
            update_creator_profile(phone, bio, insta, youtube, pic_url)
            prof = get_creator_profile(phone)
            msg = "Profile updated!"
        elif action == 'upload_reel' and session['phone'] == phone:
            cap = request.form.get('caption')
            if 'reel_file' in request.files:
                file = request.files['reel_file']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"reel_{phone}_{int(time.time())}_{filename}")
                    file.save(filepath)
                    with open(REELS_FILE, "a") as f:
                        f.write(f"{phone}|/{filepath}|{cap}\n")
                    msg = "Reel uploaded!"

    user_reels = []
    if os.path.exists(REELS_FILE):
        with open(REELS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3 and parts[0] == phone:
                    user_reels.append({"url": parts[1], "cap": parts[2]})

    cheers_earned = get_creator_cheers(phone)
    ice_earned = cheers_earned / 4.0
    rupees_earned = ice_earned / 2.0
    current_user_obj = get_user(session['phone'])
    my_balance = current_user_obj['balance'] if current_user_obj else 0

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profile - {{phone}}</title>
        <style>
            body { background: #07090e; color: white; margin: 0; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; padding-bottom: 80px; }
            .profile-card { background: #111827; width: 92%; max-width: 500px; margin-top: 15px; padding: 20px; border-radius: 16px; border: 1px solid #1e293b; text-align: center; position: relative; }
            .avatar { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 3px solid #38bdf8; margin-bottom: 10px; }
            input, textarea { width: 100%; padding: 10px; margin: 6px 0; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
            button { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 8px; width: 100%; }
            .social-links { display: flex; justify-content: center; gap: 12px; margin: 12px 0; }
            .social-btn { background: #1e293b; padding: 6px 14px; border-radius: 20px; color: #38bdf8; text-decoration: none; font-size: 12px; font-weight: bold; }
            .reels-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 15px; }
            .reel-thumb { background: #0f172a; border-radius: 8px; overflow: hidden; height: 120px; position: relative; }
            .reel-thumb video { width: 100%; height: 100%; object-fit: cover; }
            .nav-bottom { position: fixed; bottom: 0; width: 100%; height: 60px; background: #0f172a; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #1e293b; z-index: 100; }
            .nav-item { color: #94a3b8; text-decoration: none; font-size: 13px; font-weight: bold; display: flex; flex-direction: column; align-items: center; }
            .nav-item.active { color: #38bdf8; }
            .icon-btn { position: absolute; background: #1e293b; border: 1px solid #334155; color: #38bdf8; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 16px; }
            .settings-icon { top: 15px; right: 15px; }
            .plus-icon { top: 15px; left: 15px; }
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 200; justify-content: center; align-items: center; }
            .modal-content { background: #111827; padding: 20px; border-radius: 12px; width: 90%; max-width: 400px; border: 1px solid #1e293b; text-align: left; }
            .wallet-box { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 12px; margin-top: 15px; text-align: left; }
            .action-choice-btn { background: #1e293b; border: 1px solid #334155; color: white; padding: 14px; border-radius: 10px; font-weight: bold; width: 100%; margin-top: 10px; cursor: pointer; text-align: center; display: block; text-decoration: none; font-size: 15px; }
            .plan-btn { background: #0f172a; border: 1px solid #334155; color: white; padding: 8px; border-radius: 8px; cursor: pointer; text-align: left; width: 100%; }
        </style>
    </head>
    <body>
        <div class="profile-card">
            {% if session['phone'] == phone %}
            <div class="icon-btn plus-icon" onclick="openModal('actionModal')" title="Create">➕</div>
            <div class="icon-btn settings-icon" onclick="openModal('editModal')" title="Settings">⚙️</div>
            {% endif %}

            <img src="{{prof.pic}}" class="avatar">
            <h2 style="margin: 5px 0; color: #38bdf8;">@{{phone}}</h2>
            <p style="color: #94a3b8; font-size: 14px;">{{prof.bio}}</p>
            
            <div class="social-links">
                {% if prof.insta and prof.insta != '#' %}<a href="{{prof.insta}}" target="_blank" class="social-btn">📸 Instagram</a>{% endif %}
                {% if prof.youtube and prof.youtube != '#' %}<a href="{{prof.youtube}}" target="_blank" class="social-btn">▶️ YouTube</a>{% endif %}
            </div>

            {% if session['phone'] == phone %}
            <div style="background: #0f172a; border: 1px solid #38bdf8; border-radius: 10px; padding: 12px; margin-top: 10px; text-align: center;">
                <div style="font-size: 13px; color: #cbd5e1;">Game Wallet: <strong style="color: #10b981;">{{my_balance}} Cheers</strong></div>
                <button onclick="openModal('rechargeModal')" style="margin-top: 8px; background: linear-gradient(135deg, #3b82f6, #1d4ed8);">➕ Recharge Wallet</button>
            </div>
            <a href="/logout" style="display:block; margin-top:15px; font-size:12px; color:#ef4444; text-decoration:none; font-weight:bold;">🚪 Logout</a>
            {% endif %}

            <div class="wallet-box">
                <h3 style="margin:0 0 8px 0; font-size:14px; color:#10b981;">💰 Creator Earnings</h3>
                <div style="font-size:12px; color:#cbd5e1; display:flex; justify-content:space-between; margin:4px 0;">
                    <span>Gifts Received:</span> <strong style="color:#38bdf8;">{{cheers_earned}} Cheers</strong>
                </div>
                <div style="font-size:12px; color:#cbd5e1; display:flex; justify-content:space-between; margin:4px 0;">
                    <span>Rupees Worth:</span> <strong style="color:#10b981;">₹{{rupees_earned}}</strong>
                </div>
                {% if session['phone'] == phone %}
                <button onclick="openModal('withdrawModal')" style="margin-top:10px; background:#10b981; font-size:12px; padding:8px;">Withdraw Earnings</button>
                {% endif %}
            </div>

            {% if msg %}<p style="color: #10b981; font-size: 13px;">{{msg}}</p>{% endif %}

            <div style="text-align: left; margin-top: 20px;">
                <h3 style="font-size: 14px; color: #38bdf8; margin-bottom: 8px;">🎬 My Reels</h3>
                {% if user_reels|length == 0 %}
                <p style="font-size: 12px; color: #64748b;">No reels uploaded.</p>
                {% else %}
                <div class="reels-grid">
                    {% for r in user_reels %}
                    <div class="reel-thumb"><video src="{{r.url}}" muted></video></div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>

        <div id="rechargeModal" class="modal">
            <div class="modal-content" style="text-align: center; max-height: 92vh; overflow-y: auto;">
                <h3 style="margin:0 0 8px 0; color:#38bdf8; font-size: 16px;">💳 Recharge Game Wallet</h3>
                <div style="background:white; padding:6px; display:inline-block; border-radius:8px; margin-bottom: 4px;">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=upi://pay?pa=8298363286@mbkns&pn=Kamni%20Kumari&cu=INR" alt="QR" style="width:110px; height:110px; display:block;">
                </div>
                <div style="background:#0f172a; padding:4px; border-radius:6px; font-size:11px; margin-bottom:6px;">
                    UPI ID: <strong style="color:#38bdf8;" id="upiIdText">8298363286@mbkns</strong>
                    <button onclick="copyUpi()" style="background:#3b82f6; padding:2px 5px; font-size:9px; margin-left:6px; width:auto;">Copy</button>
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; margin-bottom: 8px;">
                    <button type="button" class="plan-btn" onclick="selectPlan(99, 500, this)"><b>₹99</b><br><span style="font-size:9px; color:#38bdf8;">500 Cheers</span></button>
                    <button type="button" class="plan-btn" onclick="selectPlan(350, 1600, this)"><b>₹350</b><br><span style="font-size:9px; color:#38bdf8;">1,600 Cheers</span></button>
                    <button type="button" class="plan-btn" onclick="selectPlan(700, 4000, this)"><b>₹700</b><br><span style="font-size:9px; color:#38bdf8;">4,000 Cheers</span></button>
                    <button type="button" class="plan-btn" onclick="selectPlan(1500, 8000, this)"><b>₹1,500</b><br><span style="font-size:9px; color:#38bdf8;">8,000 Cheers</span></button>
                    <button type="button" class="plan-btn" onclick="selectPlan(3750, 20000, this)"><b>₹3,750</b><br><span style="font-size:9px; color:#38bdf8;">20,000 Cheers</span></button>
                    <button type="button" class="plan-btn" onclick="selectPlan(11500, 58000, this)"><b>₹11,500</b><br><span style="font-size:9px; color:#38bdf8;">58,000 Cheers</span></button>
                </div>
                <input type="number" id="rechargeAmount" placeholder="Plan Amount (₹)" readonly style="background:#0f172a; padding: 8px; margin: 3px 0;">
                <input type="text" id="rechargeUtr" placeholder="Enter 12-digit UTR ID" style="background:#0f172a; padding: 8px; margin: 3px 0;">
                <button type="button" onclick="submitRecharge()" style="background:#10b981; margin-top:6px; padding: 10px;">Verify & Add Balance</button>
                <button type="button" onclick="closeModal('rechargeModal')" style="background:#ef4444; margin-top:4px; padding: 8px;">Close</button>
            </div>
        </div>

        <div id="actionModal" class="modal">
            <div class="modal-content" style="text-align: center;">
                <h3 style="margin-top:0; color:#38bdf8;">⚡ Creator Studio</h3>
                <button class="action-choice-btn" onclick="openModal('uploadModal'); closeModal('actionModal');" style="background:#3b82f6;">🎬 Upload Reel Video</button>
                <button class="action-choice-btn" onclick="goLive()" style="background:linear-gradient(135deg, #ef4444, #dc2626);">🔴 Start Live Stream Studio</button>
                <button type="button" onclick="closeModal('actionModal')" style="background:#334155; margin-top:15px; width:100%;">Cancel</button>
            </div>
        </div>

        <div id="editModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-top:0; color:#38bdf8;">⚙️ Edit Profile</h3>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="action" value="update_profile">
                    <label style="font-size:11px; color:#94a3b8;">Picture:</label>
                    <input type="file" name="pic_file" accept="image/*">
                    <label style="font-size:11px; color:#94a3b8;">Bio:</label>
                    <textarea name="bio" rows="2">{{prof.bio}}</textarea>
                    <label style="font-size:11px; color:#94a3b8;">Instagram:</label>
                    <input type="text" name="insta" value="{{prof.insta}}">
                    <label style="font-size:11px; color:#94a3b8;">YouTube:</label>
                    <input type="text" name="youtube" value="{{prof.youtube}}">
                    <button type="submit">Save</button>
                    <button type="button" onclick="closeModal('editModal')" style="background:#ef4444; margin-top:6px;">Cancel</button>
                </form>
            </div>
        </div>

        <div id="uploadModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-top:0; color:#10b981;">➕ Upload Reel</h3>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="action" value="upload_reel">
                    <label style="font-size:11px; color:#94a3b8;">Video File:</label>
                    <input type="file" name="reel_file" accept="video/*" required>
                    <label style="font-size:11px; color:#94a3b8;">Caption:</label>
                    <input type="text" name="caption" placeholder="Write caption..." required>
                    <button type="submit" style="background:#10b981;">Upload</button>
                    <button type="button" onclick="closeModal('uploadModal')" style="background:#ef4444; margin-top:6px;">Cancel</button>
                </form>
            </div>
        </div>

        <div id="withdrawModal" class="modal">
            <div class="modal-content">
                <h3 style="margin-top:0; color:#10b981;">💸 Withdraw Earnings</h3>
                <input type="number" id="withdrawAmount" placeholder="Amount in ₹">
                <button type="button" onclick="requestWithdraw()" style="background:#10b981;">Submit</button>
                <button type="button" onclick="closeModal('withdrawModal')" style="background:#ef4444; margin-top:6px;">Cancel</button>
            </div>
        </div>

        <div class="nav-bottom">
            <a href="/feed" class="nav-item">🏠 Feed</a>
            <a href="/live_feed" class="nav-item">🔴 Live</a>
            <a href="/game" class="nav-item">🎮 Play Game</a>
            <a href="/profile/{{session['phone']}}" class="nav-item active">👤 Profile</a>
        </div>

        <script>
            function openModal(id) { document.getElementById(id).style.display = 'flex'; }
            function closeModal(id) { document.getElementById(id).style.display = 'none'; }
            function copyUpi() {
                navigator.clipboard.writeText(document.getElementById('upiIdText').innerText);
                alert("📋 UPI ID Copied!");
            }
            function selectPlan(rupees, cheers, btn) {
                document.getElementById('rechargeAmount').value = rupees;
                document.querySelectorAll('.plan-btn').forEach(b => b.style.borderColor = '#334155');
                btn.style.borderColor = '#38bdf8';
            }
            function submitRecharge() {
                let amount = document.getElementById('rechargeAmount').value;
                let utr = document.getElementById('rechargeUtr').value;
                if(!amount || !utr) { alert("Select plan & enter UTR!"); return; }
                fetch('/recharge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount: amount, utr: utr })
                }).then(res => res.json()).then(data => {
                    if(data.success) { alert("✅ Recharge Successful!"); window.location.reload(); }
                    else { alert("❌ " + data.error); }
                });
            }
            function goLive() {
                fetch('/start_live', { method: 'POST' }).then(res => res.json()).then(data => {
                    if(data.success) { window.location.href = '/live/{{phone}}'; }
                });
            }
            function requestWithdraw() {
                let amt = document.getElementById('withdrawAmount').value;
                fetch('/withdraw', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rupees: amt })
                }).then(res => res.json()).then(data => {
                    if(data.success) { alert("✅ " + data.message); window.location.reload(); }
                    else { alert("❌ " + data.error); }
                });
            }
        </script>
    </body>
    </html>
    """, phone=phone, prof=prof, target_user=target_user, msg=msg, user_reels=user_reels, cheers_earned=cheers_earned, ice_earned=ice_earned, rupees_earned=rupees_earned, my_balance=my_balance)

@app.route('/update_bet_ajax', methods=['POST'])
def update_bet_ajax():
    if 'phone' not in session: return jsonify({'success': False, 'error': 'Unauthorized'})
    data = request.get_json()
    action, item, amount, round_id = data.get('action'), data.get('item'), int(data.get('amount', 0)), int(data.get('round_id', 0))
    user = get_user(session['phone'])
    if not user: return jsonify({'success': False, 'error': 'User not found'})
    balance = user['balance']
    user_bets = get_user_bets(session['phone'], round_id)
    current_item_bet = user_bets.get(item, 0)
    
    if action == 'add':
        if balance < amount: return jsonify({'success': False, 'error': 'Not enough balance!'})
        new_balance = balance - amount
        record_bet(session['phone'], round_id, item, amount)
    elif action == 'sub':
        if current_item_bet < amount: return jsonify({'success': False, 'error': 'No bet amount!'})
        new_balance = balance + amount
        record_bet(session['phone'], round_id, item, -amount)
    else:
        return jsonify({'success': False, 'error': 'Invalid action'})
        
    update_user_balance(session['phone'], new_balance)
    return jsonify({'success': True, 'new_balance': new_balance, 'user_bets': get_user_bets(session['phone'], round_id)})

@app.route('/claim_winnings', methods=['POST'])
def claim_winnings():
    if 'phone' not in session: return jsonify({'success': False})
    data = request.get_json()
    round_id = int(data.get('round_id', 0))
    claimed_key = f"claimed_{session['phone']}_{round_id}"
    if session.get(claimed_key): return jsonify({'success': True, 'winnings': 0})
    
    winning_item = determine_admin_profit_winning_item(round_id)
    user_bets = get_user_bets(session['phone'], round_id)
    winnings = 0
    if winning_item in user_bets:
        winnings = user_bets[winning_item] * ITEM_MULTIPLIERS[winning_item]
        
    if winnings > 0:
        user = get_user(session['phone'])
        update_user_balance(session['phone'], user['balance'] + winnings)
        
    session[claimed_key] = True
    return jsonify({'success': True, 'winnings': winnings, 'winning_item': winning_item})

@app.route('/game_status')
def game_status():
    nowSec = int(time.time())
    round_id, sec = nowSec // 25, nowSec % 25
    winning_item = determine_admin_profit_winning_item(round_id)
    item_totals = get_round_total_bets(round_id)
    
    return jsonify({
        'round_id': round_id, 'sec': sec, 'winning_item': winning_item,
        'user_bets': get_user_bets(session['phone'], round_id) if 'phone' in session else {},
        'item_totals': item_totals, 'total_collection': sum(item_totals.values()),
        'today_55x_wins': get_today_55x_wins(), 'history': get_game_history()
    })

@app.route('/game')
def game():
    if 'phone' not in session: return redirect('/login')
    user = get_user(session['phone'])
    balance = user['balance']
    round_id = int(time.time() / 25)
    winning_item = determine_admin_profit_winning_item(round_id)
    
    all_users = get_all_users()
    user_rank = "N/A"
    for idx, u in enumerate(all_users):
        if u['phone'] == session['phone']: user_rank = f"#{idx + 1}"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROVIX - Game Arena</title>
        <style>
            * { box-sizing: border-box; }
            body { background: #07090e; color: white; text-align: center; font-family: sans-serif; margin: 0; padding: 4px; width: 100vw; height: 100vh; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; }
            .card { background: #111827; width: 100%; max-width: 600px; height: calc(100% - 65px); margin: auto; padding: 6px; border-radius: 10px; border: 1px solid #1e293b; display: flex; flex-direction: column; justify-content: space-between; }
            .game-board { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; margin: 2px 0; flex-grow: 1; }
            .item { background: #1f2937; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 26px; border-radius: 8px; border: 2px solid transparent; position: relative; }
            .item.selected { border-color: #38bdf8; background: #0f172a; }
            .item.winner-box { border-color: #10b981 !important; background: #064e3b !important; }
            .badge { position: absolute; top: 2px; right: 4px; background: #f59e0b; color: #000; font-size: 9px; font-weight: bold; padding: 1px 3px; border-radius: 3px; }
            .multiplier-tag { position: absolute; bottom: 2px; font-size: 8px; color: #38bdf8; font-weight: bold; background: rgba(0,0,0,0.4); padding: 1px 2px; border-radius: 3px; }
            .controls-row { display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 1px; }
            .ctrl-btn { background: #ef4444; color: white; border: none; width: 18px; height: 18px; border-radius: 50%; font-weight: bold; cursor: pointer; font-size: 10px; display: flex; align-items: center; justify-content: center; }
            .ctrl-btn.plus { background: #10b981; }
            .center-box { background: #0f172a; border: 2px dashed #38bdf8; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 2px; }
            .chip-btn { background: #374151; color: white; border: none; padding: 4px 6px; margin: 1px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 10px; }
            .chip-btn.active { background: #f59e0b; color: #000; }
            .admin-panel { background: #0f172a; margin-top: 2px; padding: 4px; border-radius: 5px; font-size: 10px; text-align: left; border: 1px solid #334155; }
            .history-bar { background: #0f172a; padding: 4px; border-radius: 5px; display: flex; gap: 4px; overflow-x: auto; align-items: center; border: 1px solid #334155; }
            .history-item { background: #1f2937; padding: 2px 6px; border-radius: 4px; font-size: 11px; white-space: nowrap; }
            .nav-bottom { position: fixed; bottom: 0; left:0; width: 100%; height: 60px; background: #0f172a; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #1e293b; z-index: 100; }
            .nav-item { color: #94a3b8; text-decoration: none; font-size: 13px; font-weight: bold; display: flex; flex-direction: column; align-items: center; }
            .nav-item.active { color: #38bdf8; }
        </style>
    </head>
    <body>
        <div class="card">
            <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold;">
                <span style="color: #10b981;">Balance: <span id="balanceDisplay">{{balance}}</span> Cheers</span>
                <span style="color: #fbbf24;">Rank: {{user_rank}}</span>
            </div>
            
            <p id="message" style="background: #0f172a; padding: 4px; border-radius: 5px; font-size: 10px; color: #38bdf8; margin: 2px 0; display:none;"></p>
            
            <div style="display: flex; flex-direction: column; height: 100%; justify-content: space-between;">
                <div class="game-board">
                    {% for item, mult in multipliers.items() %}
                    {% if loop.index == 5 %}
                    <div class="center-box">
                        <div id="timer" style="color: #fbbf24; font-weight: bold; font-size: 9px;">Loading...</div>
                        <div id="resultDisplay" style="font-size: 18px; margin-top: 1px;">🎲</div>
                    </div>
                    {% endif %}
                    <div class="item" id="box_{{item}}">
                        <div>{{item}}</div>
                        <div class="multiplier-tag">{{mult}}x</div>
                        <div class="badge" id="badge_{{item}}" style="display:none;">0</div>
                        <div class="controls-row">
                            <button class="ctrl-btn" onclick="modifyBet('{{item}}', -1)">-</button>
                            <span id="txt_{{item}}" style="font-size: 9px; font-weight: bold; color: #cbd5e1;">0</span>
                            <button class="ctrl-btn plus" onclick="modifyBet('{{item}}', 1)">+</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <div>
                    <div style="font-size: 9px; color: #94a3b8; margin-bottom: 1px;">Select Chip:</div>
                    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
                        {% for amt in [10, 50, 100, 1000, 5000, 10000, 20000] %}
                        <button type="button" class="chip-btn {% if loop.first %}active{% endif %}" onclick="setChip({{amt}}, this)">{{amt}}</button>
                        {% endfor %}
                    </div>
                </div>
                
                <div style="font-size: 11px; color: #cbd5e1;">Total Bet: <span id="totalBetDisplay" style="color: #38bdf8; font-weight: bold;">0 Cheers</span></div>
            </div>

            <div style="text-align: left; font-size: 9px; color: #94a3b8;">History:</div>
            <div class="history-bar" id="historyBar"></div>

            <div class="admin-panel">
                <div style="font-weight: bold; color: #38bdf8; font-size:9px;">🛡️ Admin No-Loss Control:</div>
                <div style="display: flex; justify-content: space-between; font-size: 9px; color: #fbbf24;">
                    <span id="totalCollectionText">Pool: 0</span>
                    <span id="sodaWinsText">55x Wins: 0/3</span>
                </div>
            </div>
        </div>

        <div class="nav-bottom">
            <a href="/feed" class="nav-item">🏠 Feed</a>
            <a href="/live_feed" class="nav-item">🔴 Live</a>
            <a href="/game" class="nav-item active">🎮 Play Game</a>
            <a href="/profile/{{session['phone']}}" class="nav-item">👤 Profile</a>
        </div>

        <script>
            let currentChip = 10;
            let currentBalance = parseInt("{{ balance }}");
            const multipliers = {{ multipliers | tojson }};
            let currentRoundId = 0;
            let hasClaimed = false;
            
            function setChip(amount, btn) {
                currentChip = amount;
                document.querySelectorAll('.chip-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
            
            function modifyBet(item, direction) {
                let sec = Math.floor(Date.now() / 1000) % 25;
                if(sec >= 20) { showAlert("Betting closed for this round!"); return; }
                let action = direction === 1 ? 'add' : 'sub';
                if(action === 'add' && currentBalance < currentChip) { showAlert("❌ Not enough balance!"); return; }
                
                fetch('/update_bet_ajax', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action, item: item, amount: currentChip, round_id: currentRoundId })
                }).then(res => res.json()).then(data => {
                    if(data.success) {
                        currentBalance = data.new_balance;
                        document.getElementById('balanceDisplay').innerText = currentBalance;
                        updateUIBets(data.user_bets);
                    } else { showAlert("❌ " + data.error); }
                });
            }
            
            function updateUIBets(bets) {
                let total = 0;
                for(let item in multipliers) {
                    let amt = bets[item] || 0;
                    total += amt;
                    let badge = document.getElementById('badge_' + item);
                    let txt = document.getElementById('txt_' + item);
                    let box = document.getElementById('box_' + item);
                    if(amt > 0) {
                        badge.style.display = 'block'; badge.innerText = amt;
                        txt.innerText = amt; box.classList.add('selected');
                    } else {
                        badge.style.display = 'none'; txt.innerText = '0'; box.classList.remove('selected');
                    }
                }
                document.getElementById('totalBetDisplay').innerText = total + " Cheers";
            }
            
            function showAlert(msg) {
                let p = document.getElementById('message');
                p.style.display = 'block'; p.innerText = msg;
                setTimeout(() => { p.style.display = 'none'; }, 3000);
            }
            
            setInterval(() => {
                fetch('/game_status').then(res => res.json()).then(data => {
                    if(data.round_id !== currentRoundId) {
                        currentRoundId = data.round_id;
                        hasClaimed = false;
                        document.querySelectorAll('.item').forEach(el => el.classList.remove('winner-box'));
                    }
                    let sec = data.sec;
                    document.getElementById('totalCollectionText').innerText = "Pool: " + data.total_collection;
                    document.getElementById('sodaWinsText').innerText = "55x Wins: " + data.today_55x_wins + "/3";
                    
                    let hHtml = "";
                    if(data.history) { data.history.forEach(h => { hHtml += `<div class="history-item">${h.item}</div>`; }); }
                    document.getElementById('historyBar').innerHTML = hHtml;
                    
                    let timerEl = document.getElementById('timer');
                    let resultEl = document.getElementById('resultDisplay');
                    
                    if(sec < 20) {
                        timerEl.innerText = "🟢 Open (" + (20 - sec) + "s)";
                        timerEl.style.color = "#10b981";
                        resultEl.innerText = "🎲";
                        updateUIBets(data.user_bets);
                    } else {
                        timerEl.innerText = "⏳ Result (" + (25 - sec) + "s)";
                        timerEl.style.color = "#fbbf24";
                        resultEl.innerText = data.winning_item;
                        let winningBox = document.getElementById('box_' + data.winning_item);
                        if(winningBox) winningBox.classList.add('winner-box');
                        
                        if(!hasClaimed) {
                            hasClaimed = true;
                            fetch('/claim_winnings', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ round_id: currentRoundId })
                            }).then(res => res.json()).then(cData => {
                                if(cData.success && cData.winnings > 0) {
                                    showAlert("🎉 Won " + cData.winnings + " Cheers!");
                                    setTimeout(() => { window.location.reload(); }, 2000);
                                }
                            });
                        }
                    }
                });
            }, 1000);
        </script>
    </body>
    </html>
    """, balance=balance, multipliers=ITEM_MULTIPLIERS, user_rank=user_rank)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

