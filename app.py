from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-me-later'

DB_FILE = 'database.db'

def init_db():
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
    
    cursor.execute("SELECT * FROM users WHERE email='admin@test.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Главный Админ", "admin@test.com", "123", "admin")
        )
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

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
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, password, 'client')
            )
            conn.commit()
            conn.close()
            return render_template('index.html', message="Регистрация успешна! Теперь войдите.")
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
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role FROM users")
        all_users = cursor.fetchall()
        conn.close()
        return render_template('admin.html', name=session['name'], users=all_users)
    return redirect(url_for('home'))

# --- НОВЫЕ ФУНКЦИИ ДЛЯ АДМИНА ---

@app.route('/admin/delete/<int:user_id>')
def delete_user(user_id):
    # Проверяем, что это точно админ
    if 'user' in session and session['role'] == 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Удаляем пользователя по его ID
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_role/<int:user_id>')
def toggle_role(user_id):
    if 'user' in session and session['role'] == 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Если был клиентом -> станет админом, и наоборот
            new_role = 'admin' if user[0] == 'client' else 'client'
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
            conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
