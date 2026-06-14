from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-me-later'

DB_FILE = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # 2. НОВАЯ ТАБЛИЦА: Каталог товаров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image_url TEXT
        )
    ''')
    
    # Создаем главного админа, если его нет
    cursor.execute("SELECT * FROM users WHERE email='admin@test.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Главный Админ", "admin@test.com", "123", "admin")
        )
        
    # Заполняем каталог базовыми товарами (если таблица пуста)
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        initial_products = [
            ('Рукав высокого давления (РВД) 2SN DN10', 'Шланги РВД', 4500.0, 'Двухоплеточный резиновый шланг для гидравлических систем.', 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=400'),
            ('Фитинг DKOL (М18х1.5)', 'Фитинги', 850.0, 'Метрический фитинг с легким конусом 24 градуса.', 'https://images.unsplash.com/photo-1617791160505-6f006e121980?q=80&w=400'),
            ('Быстроразъемное соединение (БРС) ISO-A 1/2', 'БРС', 3200.0, 'Классическое быстроразъемное соединение для сельхозтехники.', 'https://images.unsplash.com/photo-1537462715879-360eeb61a0bc?q=80&w=400'),
            ('Обжимная муфта 2SN DN12', 'Муфты', 600.0, 'Муфта для опрессовки двухслойных рукавов.', 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?q=80&w=400')
        ]
        cursor.executemany(
            "INSERT INTO products (title, category, price, description, image_url) VALUES (?, ?, ?, ?, ?)",
            initial_products
        )
        
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    # Вытягиваем товары из базы для показа на главной
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category, price, description, image_url FROM products")
    catalog_items = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=catalog_items)

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

# --- ОБНОВЛЕННАЯ АДМИНКА (Управление пользователями + Товарами) ---
@app.route('/admin')
def admin_dashboard():
    if 'user' in session and session['role'] == 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Берем пользователей
        cursor.execute("SELECT id, name, email, role FROM users")
        all_users = cursor.fetchall()
        
        # Берем товары
        cursor.execute("SELECT id, title, category, price FROM products")
        all_products = cursor.fetchall()
        
        conn.close()
        return render_template('admin.html', name=session['name'], users=all_users, products=all_products)
    return redirect(url_for('home'))

# --- УПРАВЛЕНИЕ КАТАЛОГОМ (ДЛЯ АДМИНА) ---

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if 'user' in session and session['role'] == 'admin':
        title = request.form.get('title')
        category = request.form.get('category')
        price = float(request.form.get('price', 0))
        description = request.form.get('description')
        image_url = request.form.get('image_url') or 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=400'
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (title, category, price, description, image_url) VALUES (?, ?, ?, ?, ?)",
            (title, category, price, description, image_url)
        )
        conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user' in session and session['role'] == 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ---

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        target_user = cursor.fetchone()
        
        if target_user and target_user[0] != 'admin@test.com':
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_role/<int:user_id>', methods=['POST'])
def toggle_role(user_id):
    if 'user' in session and session['role'] == 'admin':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT role, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user and user[1] != 'admin@test.com':
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
