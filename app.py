from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2  # Вместо sqlite3 используем psycopg2 для PostgreSQL
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/requests'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    
    # 1. Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    new_columns = [
        ("phone", "TEXT"),
        ("company", "TEXT"),
        ("address", "TEXT"),
        ("inn", "TEXT")
    ]
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except:
            conn.rollback()
    
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
        conn.rollback()

    # 3. Таблица заявок (messages) с дополнительными полями
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Безопасно добавляем колонки для полноценной заявки
    msg_columns = [
        ("status", "VARCHAR(50) DEFAULT 'Новая'"),
        ("user_id", "INT"),
        ("email", "VARCHAR(255)"),
        ("total_price", "NUMERIC(10, 2) DEFAULT 0")
    ]
    for col_name, col_type in msg_columns:
        try:
            cursor.execute(f"ALTER TABLE messages ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            conn.commit()
        except:
            conn.rollback()

    # 4. Таблица товаров, привязанных к конкретной заявке (для чекбоксов и сборки)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_items (
            id SERIAL PRIMARY KEY,
            request_id INT REFERENCES messages(id) ON DELETE CASCADE,
            product_id INT,
            product_name VARCHAR(255),
            quantity INT DEFAULT 1,
            price NUMERIC(10, 2),
            is_checked BOOLEAN DEFAULT FALSE
        )
    ''')

    # 5. Таблица для прикрепленных файлов (документы, сканы, фото)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_files (
            id SERIAL PRIMARY KEY,
            request_id INT REFERENCES messages(id) ON DELETE CASCADE,
            file_name VARCHAR(255),
            file_path VARCHAR(512),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        phone = request.form.get('phone')
        company = request.form.get('company')
        address = request.form.get('address')
        inn = request.form.get('inn')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role, phone, company, address, inn) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (name, email, password, 'client', phone, company, address, inn)
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
        tab = request.args.get('tab', 'profile')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем полные данные клиента из базы
        cursor.execute("SELECT name, email, phone, company, address, inn FROM users WHERE email = %s", (session['user'],))
        client_data = cursor.fetchone()
        
        # Товары для вкладки заказа
        cursor.execute("SELECT id, title, category, price, warehouse FROM products")
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Защита, если вдруг пользователя нет в базе
        if not client_data:
            return redirect(url_for('logout'))
            
        return render_template(
            'client.html', 
            client=client_data, 
            name=client_data[0],   # Передаем имя для шапки и аватарки
            email=client_data[1],  # Передаем email
            tab=tab, 
            products=products
        )
    return redirect(url_for('home'))

@app.route('/client/order_parts', methods=['POST'])
def order_parts():
    if 'user' in session and session['role'] == 'client':
        # Получаем списки выбранных товаров и их количество из формы
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        order_details = []
        for p_id, qty in zip(product_ids, quantities):
            if p_id and int(qty) > 0:
                # Узнаем название товара из базы по его ID
                cursor.execute("SELECT title FROM products WHERE id = %s", (p_id,))
                prod = cursor.fetchone()
                if prod:
                    order_details.append(f"{prod[0]} — {qty} шт.")
        
        if order_details:
            items_str = ", ".join(order_details)
            user_name = session['name']
            user_email = session['user']
            full_message = f"[Заказ комплектующих] Состав: {items_str} (Клиент: {user_name}, {user_email})"
            
            cursor.execute(
                "INSERT INTO messages (name, phone, message) VALUES (%s, %s, %s)",
                (user_name, "Из кабинета (комплектующие)", full_message)
            )
            conn.commit()
            
        cursor.close()
        conn.close()
        
    return redirect(url_for('client_dashboard', tab='calc'))

@app.route('/admin')
def admin_dashboard():
    if 'user' in session and session['role'] == 'admin':
        tab = request.args.get('tab', 'products')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Получаем пользователей со всеми новыми полями анкеты
        cursor.execute("SELECT id, name, email, role, phone, company, address, inn FROM users")
        all_users = cursor.fetchall()
        
        # 2. Получаем товары
        cursor.execute("SELECT * FROM products")
        all_products = cursor.fetchall()
        
        # Готовим структуру для дерева склада
        tree_data = {}
        for p in all_products:
            wh = p[6] if p[6] else 'Офис'
            cat_path = p[2].split('/')
            parent = cat_path[0]
            sub = cat_path[1] if len(cat_path) > 1 else "Прочее"
            
            if wh not in tree_data: tree_data[wh] = {}
            if parent not in tree_data[wh]: tree_data[wh][parent] = {}
            if sub not in tree_data[wh][parent]: tree_data[wh][parent][sub] = []
            
            tree_data[wh][parent][sub].append(p)
        
        # 3. Автоматически создаем колонку status, если её ещё нет в базе
        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Новая'")
        conn.commit()

        # 4. Получаем заявки (сообщения) вместе со статусом
        cursor.execute("SELECT id, name, phone, message, created_at, status FROM messages ORDER BY created_at DESC")
        all_messages = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin.html', name=session['name'], 
                               users=all_users, products=all_products, 
                               messages=all_messages, tab=tab, tree_data=tree_data)
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

@app.route('/admin/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if 'user' in session and session['role'] == 'admin':
        # Получаем данные из формы
        title = request.form.get('title')
        category = request.form.get('category')
        price = float(request.form.get('price', 0))
        warehouse = request.form.get('warehouse')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE products SET title=%s, category=%s, price=%s, warehouse=%s WHERE id=%s",
            (title, category, price, warehouse, product_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard', tab='sklad'))

@app.route('/update_request_status/<int:req_id>', methods=['POST'])
def update_request_status(req_id):
    if 'user' in session and session['role'] == 'admin':
        new_status = request.form.get('status')
        conn = get_db_connection()
        cursor = conn.cursor()
        # Автоматически добавляем колонку, если ее вдруг еще нет в базе
        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Новая'")
        cursor.execute("UPDATE messages SET status = %s WHERE id = %s", (new_status, req_id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard', tab='requests'))

@app.route('/delete_request/<int:req_id>', methods=['POST'])
def delete_request(req_id):
    if 'user' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = %s", (req_id,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('admin_dashboard', tab='requests'))

@app.route('/admin/request/<int:req_id>')
def view_request_detail(req_id):
    if 'user' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем данные заявки
        cursor.execute("SELECT id, name, phone, message, created_at, status, email, total_price FROM messages WHERE id = %s", (req_id,))
        req = cursor.fetchone()
            
        # Получаем привязанные товары (ID, название, количество, цена, статус галочки)
        cursor.execute("SELECT id, product_name, quantity, price, is_checked FROM request_items WHERE request_id = %s", (req_id,))
        items = cursor.fetchall()
        
        # Получаем прикрепленные файлы
        cursor.execute("SELECT id, file_name, file_path, uploaded_at FROM request_files WHERE request_id = %s", (req_id,))
        files = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('request_detail.html', req=req, items=items, files=files)
    return redirect(url_for('home'))

@app.route('/admin/request/<int:req_id>/update_item/<int:item_id>', methods=['POST'])
def update_request_item_check(req_id, item_id):
    if 'user' in session and session['role'] == 'admin':
        is_checked = 'is_checked' in request.form
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE request_items SET is_checked = %s WHERE id = %s AND request_id = %s", (is_checked, item_id, req_id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('view_request_detail', req_id=req_id))

@app.route('/admin/request/<int:req_id>/upload_file', methods=['POST'])
def upload_request_file(req_id):
    if 'user' in session and session['role'] == 'admin':
        file = request.files.get('file')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, f"{req_id}_{filename}")
            file.save(file_path)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO request_files (request_id, file_name, file_path) VALUES (%s, %s, %s)", 
                           (req_id, filename, f"/{file_path}"))
            conn.commit()
            cursor.close()
            conn.close()
    return redirect(url_for('view_request_detail', req_id=req_id))

@app.route('/admin/request/<int:req_id>/delete_file/<int:file_id>', methods=['POST'])
def delete_request_file(req_id, file_id):
    if 'user' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM request_files WHERE id = %s AND request_id = %s", (file_id, req_id))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('view_request_detail', req_id=req_id))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
