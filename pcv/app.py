from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import re
import hashlib
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']  # Store plain text password

        # Validate input data here (add your own rules)
        if not re.match(r'[A-Za-z0-9]+', name):
            flash('Username must contain only characters and numbers!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long!')
        else:
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, password))  # Store plain text password
            mysql.connection.commit()
            cursor.close()
            flash('You have successfully registered!')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # Use plain text password

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        cursor.close()

        if account and account[3] == password:  # Assuming account[3] is the plain text password
            session['loggedin'] = True
            session['id'] = account[0]  # Assuming account[0] is the user ID
            session['name'] = account[1]  # Assuming account[1] is the user's name
            return redirect(url_for('blog'))  # Redirect to blog page after successful login
        else:
            flash('Incorrect email/password!')

    return render_template('login.html')

@app.route('/blog', methods=['GET', 'POST'])
def blog():
    if request.method == 'POST':
        content = request.form.get('content')  # Use get() to avoid KeyError
        user_id = session.get('id')  # Get user ID from session
        
        if user_id is None:
            flash("You must be logged in to post a blog.")
            return redirect(url_for('login'))  # Redirect to login if no user ID

        if not content:
            flash("Content cannot be empty!")
            return redirect(url_for('blog'))

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO blogs (user_id, content) VALUES (%s, %s)", (user_id, content))
            mysql.connection.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
            flash("An error occurred while trying to save your blog entry.")
        finally:
            cur.close()

        return redirect(url_for('blog'))

    # Fetch existing blog entries
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blogs ORDER BY created_at DESC")
    entries = cur.fetchall()
    cur.close()
    
    return render_template('blog.html', entries=entries)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        content = request.form['content']
        cur.execute("UPDATE blogs SET content = %s WHERE id = %s", (content, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('blog'))

    cur.execute("SELECT * FROM blogs WHERE id = %s", (id,))
    entry = cur.fetchone()
    cur.close()
    
    return render_template('edit.html', entry=entry)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blogs WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('blog'))

@app.route('/logout', methods=['POST'])
def logout():
    # Logic to handle user logout (e.g., clearing session)
    session.pop('loggedin', None)
    session.pop('id', None)  # Clear user ID from session
    return redirect(url_for('login'))  # Redirect to login page after logout

if __name__ == "__main__":
    app.run(debug=True)