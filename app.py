from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-me-later'

DB_FILE = 'database.db'

def init_db():
    """Функция для создания базы данных и таблицы пользователей при запуске"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Создаем тестового админа, если таблицы были пустыми
    cursor.execute("SELECT * FROM users WHERE email='admin@test.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Главный Админ", "admin@test.com", "123", "admin")
        )
    conn.commit()
    conn.close()

# Запускаем создание базы данных
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, role, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[2] == password:
        session['user'] = email
        session['name'] = user[0]
        session['role'] = user[1]
        
        if user[1] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    
    return render_template('index.html', error="Неверный логин или пароль")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Все новые пользователи по умолчанию получают роль 'client'
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, password, 'client')
            )
            conn.commit()
            conn.close()
            return render_template('index.html', message="Регистрация успешна! Теперь вооидите.")
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="Пользователь с таким Email уже существует")
            
    return render_template('register.html')

@app.route('/client')
def client_dashboard():
    if 'user' in session and session['role'] == 'client':
        return render_template('client.html', name=session['name'])
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    if 'user' in session and session['role'] == 'admin':
        # Вытащим из базы список всех пользователей, чтобы админ их видел
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role FROM users")
        all_users = cursor.fetchall()
        conn.close()
        return render_template('admin.html', name=session['name'], users=all_users)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
