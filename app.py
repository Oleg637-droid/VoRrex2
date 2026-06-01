from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Секретный ключ нужен для работы сессий (чтобы сайт "помнил" вошедшего пользователя)
app.secret_key = 'super-secret-key-change-me-later'

# Симуляция базы данных (пока храним пользователей прямо в памяти сервера)
# Пароли в реальных проектах всегда шифруют, но для теста пишем текстом
USERS = {
    "admin@test.com": {"password": "123", "role": "admin", "name": "Администратор"},
    "user@test.com": {"password": "456", "role": "client", "name": "Иван Иванов"}
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Проверяем, есть ли пользователь в нашей "базе данных"
        user = USERS.get(email)
        if user and user['password'] == password:
            # Записываем пользователя в сессию
            session['user'] = email
            session['role'] = user['role']
            session['name'] = user['name']
            
            # Перенаправляем в зависимости от роли
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('client_dashboard'))
        else:
            return render_template('index.html', error="Неверный логин или пароль")
            
    return redirect(url_for('home'))

@app.route('/client')
def client_dashboard():
    if 'user' in session and session['role'] == 'client':
        return render_template('client.html', name=session['name'])
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    if 'user' in session and session['role'] == 'admin':
        return render_template('admin.html', name=session['name'])
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
