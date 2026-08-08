from flask import Flask, render_template_string, request, redirect, url_for, make_response, session
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "rovix_secret_key_xyz"

MY_UPI_ID = "8298363286@mbkns" 
MY_NAME = "Kamni Kumari"
ADMIN_PIN = "7860"

USERS_FILE = "users.txt"
PENDING_FILE = "pending.txt"
HISTORY_FILE = "history.txt"

def get_user(phone):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 3 and parts[0] == phone:
                return {"phone": parts[0], "password": parts[1], "balance": int(parts[2])}
    return None

def save_user(phone, password, balance=100):
    users = []
    updated = False
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    if parts[0] == phone:
                        users.append(f"{phone}|{password}|{balance}\n")
                        updated = True
                    else:
                        users.append(line)
    if not updated:
        users.append(f"{phone}|{password}|{balance}\n")
    with open(USERS_FILE, "w") as f:
        f.writelines(users)

def update_user_balance(phone, amount_added):
    if not os.path.exists(USERS_FILE):
        return
    users = []
    with open(USERS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 3 and parts[0] == phone:
                new_bal = int(parts[2]) + amount_added
                users.append(f"{parts[0]}|{parts[1]}|{new_bal}\n")
            else:
                users.append(line)
    with open(USERS_FILE, "w") as f:
        f.writelines(users)

def add_pending(phone, cheers, amt):
    req_id = str(os.urandom(4).hex())
    with open(PENDING_FILE, "a") as f:
        f.write(f"{req_id}|{phone}|{cheers}|{amt}\n")

def get_pending_detailed():
    if not os.path.exists(PENDING_FILE):
        return []
    with open(PENDING_FILE, "r") as f:
        lines = f.readlines()
    requests = []
    for line in lines:
        parts = line.strip().split("|")
        if len(parts) >= 4:
            requests.append({"id": parts[0], "phone": parts[1], "cheers": parts[2], "amount": parts[3]})
        elif len(parts) == 3:
            requests.append({"id": parts[0], "phone": "Unknown", "cheers": parts[1], "amount": parts[2]})
    return requests

def remove_pending(req_id):
    lines_to_keep = []
    approved_data = None
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if parts[0] == req_id:
                    approved_data = parts
                else:
                    lines_to_keep.append(line)
        with open(PENDING_FILE, "w") as f:
            f.writelines(lines_to_keep)
    return approved_data

def add_history(phone, cheers, amt):
    time_str = datetime.now().strftime("%d-%m-%Y %H:%M")
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{time_str}|{phone}|{amt}|{cheers}\n")

def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    history = []
    for line in reversed(lines):
        parts = line.strip().split("|")
        if len(parts) >= 4:
            history.append({"time": parts[0], "phone": parts[1], "amount": parts[2], "cheers": parts[3]})
    return history

@app.route('/')
def home():
    if 'phone' not in session:
        return redirect(url_for('login'))
    
    user = get_user(session['phone'])
    balance = user['balance'] if user else 0

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ROVIX Pro Hub</title>
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 15px; margin: 0; }
            .card { background: #1e293b; padding: 15px; margin: 12px auto; max-width: 400px; border-radius: 12px; }
            .btn { background: #3b82f6; color: white; padding: 12px; border: none; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 8px; font-weight: bold; text-decoration: none; display: inline-block; box-sizing: border-box; }
            .packs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        </style>
    </head>
    <body>
        <h1>🚀 ROVIX Pro Gaming</h1>
        <p style="color: #94a3b8;">Welcome, {{ phone }} | <a href="/logout" style="color: #ef4444; text-decoration: none;">Logout</a></p>
        
        <div class="card">
            <h3>💰 My Wallet Balance</h3>
            <h2 style="color: #10b981;">{{ balance }} Cheers</h2>
        </div>

        <div class="card">
            <h3>🎮 Games & Creator Zone</h3>
            <p style="color: #94a3b8; font-size: 14px;">Games & Profiles coming up next!</p>
            <a href="#" class="btn" style="background: #8b5cf6;">Play Games (Soon)</a>
            <a href="#" class="btn" style="background: #ec4899;">Creator Profile (Soon)</a>
        </div>

        <div class="card">
            <h3>💎 Recharge Packs</h3>
            <form action="/pay" method="POST">
                <div class="packs">
                    <button class="btn" name="amount" value="99" style="background: #334155;">₹99 (500)</button>
                    <button class="btn" name="amount" value="350" style="background: #334155;">₹350 (2k)</button>
                    <button class="btn" name="amount" value="800" style="background: #334155;">₹800 (4k)</button>
                    <button class="btn" name="amount" value="1500" style="background: #334155;">₹1500 (7.5k)</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """, balance=balance, phone=session['phone'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        action = request.form.get('action')
        
        if action == 'register':
            if get_user(phone):
                error = "Phone number already registered! Please Login."
            else:
                save_user(phone, password, 100) # Signup bonus 100 cheers
                session['phone'] = phone
                return redirect(url_for('home'))
        else:
            user = get_user(phone)
            if user and user['password'] == password:
                session['phone'] = phone
                return redirect(url_for('home'))
            else:
                error = "Invalid Phone Number or Password!"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - ROVIX Pro</title>
        <style>
            body { background: #0f172a; color: white; font-family: sans-serif; text-align: center; padding: 40px 15px; }
            .card { background: #1e293b; padding: 20px; max-width: 350px; margin: auto; border-radius: 12px; }
            input { width: 90%; padding: 12px; margin: 8px 0; border-radius: 6px; border: none; background: #334155; color: white; font-size: 15px; box-sizing: border-box; }
            .btn { background: #3b82f6; color: white; padding: 12px; border: none; border-radius: 6px; width: 90%; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 15px; }
        </style>
    </head>
    <body>
        <h2>🔐 ROVIX Pro Portal</h2>
        <div class="card">
            {% if error %}<p style="color: #ef4444; font-size: 14px;">{{ error }}</p>{% endif %}
            <form method="POST">
                <input type="text" name="phone" placeholder="Phone Number" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit" name="action" value="login" class="btn" style="background: #10b981;">Login</button>
                <button type="submit" name="action" value="register" class="btn" style="background: #6366f1;">Sign Up (Get 100 Cheers)</button>
            </form>
        </div>
    </body>
    </html>
    """, error=error)

@app.route('/logout')
def logout():
    session.pop('phone', None)
    return redirect(url_for('login'))

@app.route('/pay', methods=['POST'])
def pay():
    if 'phone' not in session:
        return redirect(url_for('login'))
    amt = request.form.get('amount', '99')
    mapping = {"99": 500, "350": 2000, "800": 4000, "1500": 7500, "3700": 18000}
    cheers = mapping.get(amt, 500)
    upi_link = f"upi://pay?pa={MY_UPI_ID}&pn={MY_NAME}&am={amt}&cu=INR&tn=Recharge"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={upi_link}"
    return render_template_string("""
    <body style="background: #0f172a; color: white; text-align: center; padding: 20px; font-family: sans-serif;">
        <h2>Scan to Pay ₹{{amt}}</h2>
        <img src="{{qr}}" style="background: white; padding: 10px; border-radius: 8px;">
        <p>UPI: {{upi}}</p>
        <a href="{{link}}" style="background: #10b981; padding: 12px; color: white; display: block; border-radius: 8px; text-decoration: none; max-width: 300px; margin: auto; font-weight: bold;">Pay via UPI App</a>
        <form action="/submit_proof" method="POST" style="margin-top: 15px;">
            <input type="hidden" name="cheers" value="{{cheers}}">
            <input type="hidden" name="amount" value="{{amt}}">
            <button type="submit" style="background: #f59e0b; padding: 12px; color: white; border: none; width: 300px; border-radius: 8px; font-weight: bold; cursor: pointer;">I Have Paid</button>
        </form>
    </body>
    """, amt=amt, cheers=cheers, upi=MY_UPI_ID, qr=qr_api, link=upi_link)

@app.route('/submit_proof', methods=['POST'])
def submit_proof():
    if 'phone' not in session:
        return redirect(url_for('login'))
    add_pending(session['phone'], request.form.get('cheers'), request.form.get('amount'))
    return "<body style='background:#0f172a; color:white; text-align:center; padding-top:50px; font-family:sans-serif;'><h2>⏳ Submitted Successfully!</h2><a href='/' style='color:#38bdf8;'>Go Back</a></body>"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('pin') == ADMIN_PIN:
            resp = make_response(redirect('/admin'))
            resp.set_cookie('admin_auth', 'true')
            return resp
    if request.cookies.get('admin_auth') != 'true':
        return '<body style="background:#0f172a; color:white; text-align:center; padding-top:50px; font-family:sans-serif;"><h2>Admin Login</h2><form method="POST"><input type="password" name="pin" placeholder="Enter PIN" style="padding:10px; border-radius:6px; border:none;"><button style="padding:10px 20px; background:#3b82f6; color:white; border:none; border-radius:6px; margin-left:5px;">Login</button></form></body>'
    
    pending = get_pending_detailed()
    history = get_history()
    
    return render_template_string("""
    <body style="background: #0f172a; color: white; padding: 20px; font-family: sans-serif; text-align: center;">
        <h2>⚡ Admin Dashboard</h2>
        <hr style="max-width: 400px; border-color: #334155;">
        <h3>⏳ Pending Approvals</h3>
        {% for r in pending %}
        <div style="background: #1e293b; border: 1px solid #334155; padding: 10px; margin: 8px auto; max-width: 380px; border-radius: 8px;">
            <p><b>User:</b> {{r.phone}} | <b>₹{{r.amount}}</b> (+{{r.cheers}} Cheers)</p>
            <a href="/approve?id={{r.id}}" style="background: #10b981; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold;">Approve</a>
        </div>
        {% endfor %}
        {% if not pending %}<p style="color: #94a3b8;">No pending requests.</p>{% endif %}
        
        <h3>📜 History</h3>
        {% for h in history %}
        <div style="background: #1e293b; padding: 8px; margin: 6px auto; max-width: 380px; border-radius: 6px; font-size: 13px; text-align: left;">
            <span style="color: #94a3b8;">{{h.time}}</span> | <b>{{h.phone}}</b> paid ₹{{h.amount}} (+{{h.cheers}})
        </div>
        {% endfor %}
        <br><a href="/" style="color: #38bdf8; text-decoration: none;">← Home</a>
    </body>
    """, pending=pending, history=history)

@app.route('/approve')
def approve():
    if request.cookies.get('admin_auth') != 'true':
        return redirect('/admin')
    req_id = request.args.get('id')
    data = remove_pending(req_id)
    if data:
        phone = data[1]
        cheers = int(data[2])
        amt = data[3] if len(data) > 3 else "99"
        update_user_balance(phone, cheers)
        add_history(phone, cheers, amt)
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

