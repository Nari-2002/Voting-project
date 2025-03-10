from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key for session management

# Set up database URI using SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:nari@localhost/EC'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model to match the 'users_logins' table
class User(db.Model):
    user_name = db.Column(db.String(255), primary_key=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<User {self.user_name}>'

# Function to authenticate user using SQLAlchemy
def authenticate_user(username, password):
    user = User.query.filter_by(user_name=username).first()  # Query for the username
    if user and user.password == password:  # Check if password matches
        return True
    return False

# Home route for login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if authenticate_user(username, password):
            session['user_name'] = username  # Store username in session
            return redirect(url_for('dashboard'))  # Redirect to dashboard if login is successful
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    # if 'user_name' not in session:  # Check if user is logged in
    #     flash('Please log in to access the dashboard.', 'warning')
    #     return redirect(url_for('login'))
    
    return render_template('dashboard.html')  # Show dashboard page

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_name', None)  # Remove user_name from session
    return redirect(url_for('login'))  # Redirect to login page after logging out

if __name__ == '__main__':
    app.run(debug=True)
