from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def get_db_connection():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usuario, senha))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user'] = usuario
            return redirect(url_for('hello'))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos.')

    return render_template('login.html')

@app.route('/hello')
def hello():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('hello.html', usuario=session['user'])

if __name__ == '__main__':
    app.run(debug=True)
