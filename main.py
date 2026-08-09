from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Rovix Arena Game Reels App is Live!"

def run_game_app():
    # Tumhara game reels wala logic yahan run hoga
    print("Game reels application started successfully.")

if __name__ == '__main__':
    # Background mein game logic chalega aur Flask server live rahega
    threading.Thread(target=run_game_app, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
