from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
# Set up database URI using SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:nari@localhost/EC2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model to match the 'users_logins' table
class User(db.Model):
    user_name = db.Column(db.String(255), primary_key=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<User {self.user_name}>'
# Define the Constituency model
class Constituencies(db.Model):
    __tablename__ = 'constituencies'  # Explicitly set the table name
    code = db.Column(db.String(10), primary_key=True)  # Use 'code' as the primary key
    name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Constituency {self.name}>'

# Define the Party model
class Parties(db.Model):
    __tablename__ = 'parties'  # Explicitly set the table name

    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(255))  # Optional: if you still want to use it
    link = db.Column(db.String(255))  # This will store the image URL
    no_of_votes = db.Column(db.Integer, default=0)
    constituency_code = db.Column(db.String(10), db.ForeignKey('constituencies.code'), nullable=False)
    party_name = db.Column(db.String(255), nullable=False)  # Added party_name column

    constituency = db.relationship('Constituencies', backref=db.backref('parties', lazy=True))

    # Ensure that each party has only one candidate per constituency
    __table_args__ = (
        db.UniqueConstraint('party_name', 'constituency_code', name='_party_constituency_uc'),
    )

    def __repr__(self):
        return f'<Party {self.party_name} ({self.candidate_name})>'



# Define the Voter model
class Voters(db.Model):
    __tablename__ = 'voters'  # Explicitly set the table name
    voter_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    constituency_code = db.Column(db.String(10), db.ForeignKey('constituencies.code'), nullable=False)  # Use constituency_code as the foreign key
    is_voted = db.Column(db.Boolean, default=False)

    constituency = db.relationship('Constituencies', backref=db.backref('voters', lazy=True))

    def __repr__(self):
        return f'<Voter {self.name}>'

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
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_name' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    constituencies = Constituencies.query.all()  # Fetch all constituencies for dropdown
    if request.method == 'POST':
        selected_constituency = request.form['constituency']
        return redirect(url_for('voter_id', constituency_code=selected_constituency))

    return render_template('dashboard.html', constituencies=constituencies)
@app.route('/voter_id/<string:constituency_code>', methods=['GET', 'POST'])
def voter_id(constituency_code):
    # Fetch constituency by code
    constituency = Constituencies.query.filter_by(code=constituency_code).first()

    # Handle case where constituency does not exist
    if not constituency:
        flash('Constituency not found.', 'danger')
        return redirect(url_for('dashboard'))

    # Fetch voter based on voter ID if form is submitted
    if request.method == 'POST':
        # Safely get the voter ID from form input
        voter_id = request.form.get('voter_id').upper()

        # Validate voter ID
        if not voter_id:
            flash('Voter ID cannot be empty.', 'danger')
            return render_template('voter_id.html', constituency=constituency)

        # Check if voter exists in the database
        voter = Voters.query.filter_by(voter_id=voter_id, constituency_code=constituency.code).first()

        if voter:
            # Check if the voter has already voted
            if voter.is_voted:
                flash('You have already voted in this constituency.', 'danger')
                return redirect(url_for('voter_id', constituency_code=constituency_code))
            else:
                # If voter hasn't voted, redirect to the candidates page
                return redirect(url_for('display_candidates', constituency_code=constituency.code, voter_id=voter_id))
        else:
            flash('Invalid voter ID for this constituency.', 'danger')

    # Render the voter ID page if GET request or after a failed POST request
    return render_template('voter_id.html', constituency=constituency)



#display details
@app.route('/display_candidates/<string:constituency_code>/<string:voter_id>', methods=['GET', 'POST'])
def display_candidates(constituency_code, voter_id):
    constituency = Constituencies.query.get(constituency_code)
    party = Parties.query.filter_by(constituency_code=constituency_code).all()  # Fetching all parties
    voter = Voters.query.filter_by(voter_id=voter_id).first()

    if request.method == 'POST':
        party_id = request.form['party_id']
        selected_party = Parties.query.get(party_id)  # Get the selected party

        if not voter.is_voted:
            selected_party.no_of_votes += 1
            voter.is_voted = True
            db.session.commit()
            flash('Vote submitted successfully!', 'success')
            return redirect(url_for('voter_id', constituency_code=constituency_code))
        else:
            flash('You have already voted.', 'danger')
            return redirect(url_for('voter_id', constituency_code=constituency_code))

    return render_template('display_candidates.html', party=party, constituency=constituency, voter=voter)


# Logout route
@app.route('/logout')
def logout():
    #session.pop('user_name', None)  # Remove user_name from session
    return redirect(url_for('login'))  # Redirect to login page after logging out

if __name__ == '__main__':
    with app.app_context():  # Ensure the app context is active for database operations
        db.create_all()  # Create tables in the database
    app.run(debug=True)

