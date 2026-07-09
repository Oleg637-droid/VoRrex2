from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2  # Вместо sqlite3 используем psycopg2 для PostgreSQL

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-me-later'

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ RENDER ---
# На Render строку подключения лучше брать из переменных окружения.
# Локально (на компьютере) вставьте вашу скопированную строку Internal/External URL вместо 'ваша_строка_от_render'
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://vortex_admin:5kevZJOhBN9sGTxkYUVnqnfWZrb3YL8x@dpg-d8n6cfkm0tmc73dpedh0-a/vortex_qfmw')

def get_db_connection():
    # Функция для быстрого подключения к PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Таблица пользователей (в Postgres синтаксис немного отличается: SERIAL вместо AUTOINCREMENT)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # 2. Таблица Каталога товаров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image_url TEXT
        )
    ''')
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN warehouse TEXT DEFAULT 'Офис'")
        conn.commit()
    except:
        conn.rollback() # Если колонка уже есть, просто пропускаем ошибку
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Создаем главного админа, если его нет
    cursor.execute("SELECT * FROM users WHERE email='admin@test.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            ("Главный Админ", "admin@test.com", "123", "admin")
        )
        
    # Заполняем каталог базовыми товарами (если пуст)
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        initial_products = [
            ('Рукав высокого давления (РВД) 2SN DN10', 'Шланги РВД', 4500.0, 'Двухоплеточный резиновый шланг для гидравлических систем.', 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=400'),
            ('Фитинг DKOL (М18х1.5)', 'Фитинги', 850.0, 'Метрический фитинг с легким конусом 24 градуса.', 'https://images.unsplash.com/photo-1617791160505-6f006e121980?q=80&w=400'),
            ('Быстроразъемное соединение (БРС) ISO-A 1/2', 'БРС', 3200.0, 'Классическое быстроразъемное соединение для сельхозтехники.', 'https://images.unsplash.com/photo-1537462715879-360eeb61a0bc?q=80&w=400'),
            ('Обжимная муфта 2SN DN12', 'Муфты', 600.0, 'Муфта для опрессовки двухслойных рукавов.', 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?q=80&w=400')
        ]
        cursor.executemany(
            "INSERT INTO products (title, category, price, description, image_url) VALUES (%s, %s, %s, %s, %s)",
            initial_products
        )
        
    conn.commit()
    cursor.close()
    conn.close()

# Запускаем инициализацию при старте
init_db()

@app.route('/')
def home():
    return render_template('index.html')

from flask import render_template, request

@app.route('/catalog')
def catalog():
    category = request.args.get('category') # Получаем категорию из ссылки, если есть
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Если выбрана категория — фильтруем, если нет — показываем всё
    if category:
        cur.execute("SELECT * FROM products WHERE category = %s", (category,))
    else:
        cur.execute("SELECT * FROM products")
        
    products = cur.fetchall()
    
    # Также получаем список уникальных категорий для сайдбара
    cur.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return render_template('catalog.html', products=products, categories=categories, current_category=category)

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        msg = request.form.get('message')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (name, phone, message) VALUES (%s, %s, %s)", (name, phone, msg))
        conn.commit()
        cur.close()
        conn.close()
        return "Спасибо, заявка принята!" # Или перенаправь на главную
        
    return render_template('contacts.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, role, password FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, 'client')
            )
            conn.commit()
            cursor.close()
            conn.close()
            return render_template('index.html', message="Регистрация успешна! Теперь войдите.")
        except psycopg2.IntegrityError:
            cursor.close()
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
        tab = request.args.get('tab', 'products')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Запрос пользователей
        cursor.execute("SELECT id, name, email, role FROM users")
        all_users = cursor.fetchall()
        
        # Запрос товаров
        cursor.execute("SELECT id, title, category, price FROM products")
        all_products = cursor.fetchall()
        
        # --- ДОБАВЛЯЕМ ЗАПРОС ЗАЯВОК ---
        cursor.execute("SELECT id, name, phone, message, created_at FROM messages ORDER BY created_at DESC")
        all_messages = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Передаем all_messages в шаблон
        return render_template('admin.html', name=session['name'], 
                               users=all_users, products=all_products, 
                               messages=all_messages, tab=tab)
    return redirect(url_for('home'))

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if 'user' in session and session['role'] == 'admin':
        title = request.form.get('title')
        category = request.form.get('category')
        price = float(request.form.get('price', 0))
        warehouse = request.form.get('warehouse') # Получаем склад
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # Добавляем в запрос новое поле warehouse
        cursor.execute(
            "INSERT INTO products (title, category, price, warehouse) VALUES (%s, %s, %s, %s)",
            (title, category, price, warehouse)
        )
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard', tab='products'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
