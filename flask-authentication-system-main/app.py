from flask import Flask, request, render_template, redirect, session,url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'student'
app.config['MYSQL_PASSWORD'] = 'student'
app.config['MYSQL_DB'] = 'dipraj'

mysql = MySQL(app)

# Create the tables in the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password == confirm_password:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (name, password, email))
            mysql.connection.commit()
            cur.close()
            return redirect('/login?registration=success')  # Redirect to login with a success message

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and User(email, password, user[2]).check_password(password):
            session['email'] = email
            return redirect('/home')
        else:
            return render_template('login.html', error='Invalid user')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        email = session['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            return render_template('dashboard.html', user=user)
    
    return redirect('/login')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/send_reminder', methods=['POST'])
def send_reminder():
    if request.method == 'POST':
        message = request.form['message']
        date = request.form['date']
        time = request.form['time']
        classes = ', '.join(request.form.getlist('classes'))
        teacher = request.form['teacher']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO reminders (message, date, time, classes, teacher) VALUES (%s, %s, %s, %s, %s)",
                    (message, date, time, classes, teacher))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
