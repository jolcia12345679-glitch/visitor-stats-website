from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import sqlite3
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Administrator credentials (bez hashowania)
ADMIN_LOGIN = 'ZZpln'
ADMIN_PASSWORD = 'Qazxsw123'

# Database path
DB_PATH = 'visitor_stats.db'

def init_db():
    """Initialize database"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE visits (
                id INTEGER PRIMARY KEY,
                visit_date TEXT NOT NULL,
                visit_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator for login requirement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def record_visit():
    """Record a visitor"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('SELECT * FROM visits WHERE visit_date = ?', (today,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute('UPDATE visits SET visit_count = visit_count + 1 WHERE visit_date = ?', (today,))
    else:
        cursor.execute('INSERT INTO visits (visit_date, visit_count) VALUES (?, 1)', (today,))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main page with authorization error"""
    record_visit()
    return render_template('error.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = login
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Błędny login lub hasło')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all visits sorted by date
    cursor.execute('SELECT * FROM visits ORDER BY visit_date DESC')
    visits = cursor.fetchall()
    
    # Calculate total visits
    cursor.execute('SELECT SUM(visit_count) as total FROM visits')
    total_result = cursor.fetchone()
    total_visits = total_result['total'] if total_result['total'] else 0
    
    conn.close()
    
    return render_template('dashboard.html', visits=visits, total_visits=total_visits)

@app.route('/reset-day/<date>', methods=['POST'])
@login_required
def reset_day(date):
    """Reset visits for a specific day"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM visits WHERE visit_date = ?', (date,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)