from flask import Flask, flash, redirect, request, render_template, url_for
import pymysql
import boto3
import requests

app = Flask(__name__)

import requests

def get_aws_region():
    metadata_url = "http://169.254.169.254/latest/dynamic/instance-identity/document"
    response = requests.get(metadata_url)
    metadata = response.json()
    return metadata['region']

# Get the AWS region
region = get_aws_region()


def get_db_connection():
    # Initialize AWS SDK
    session = boto3.session.Session()
    ssm_client = session.client('ssm', region_name=region)

    # Fetch database details from Parameter Store
    db_host = ssm_client.get_parameter(Name='/myapp/db_endpoint', WithDecryption=True)['Parameter']['Value']
    db_user = ssm_client.get_parameter(Name='/myapp/db_user', WithDecryption=True)['Parameter']['Value']
    db_password = ssm_client.get_parameter(Name='/myapp/db_password', WithDecryption=True)['Parameter']['Value']
    db_name = ssm_client.get_parameter(Name='/myapp/db_name', WithDecryption=True)['Parameter']['Value']

    return pymysql.connect(host=db_host, user=db_user, password=db_password, db=db_name)
    #return pymysql.connect(host=db_host, user=db_user, password=db_password)

def create_table():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create a 'users' table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        password VARCHAR(50) NOT NULL
    )
    """
    cursor.execute(create_table_query)

    connection.commit()
    cursor.close()
    connection.close()

# Call create_table() when the application starts
create_table()

@app.route('/')
def home():
    #return 'Welcome to the home page!'
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        
        user = cursor.fetchone()
        
        if user:
            return "Login Successful!"
        else:
            return "Invalid credentials. Please try again."
        
        cursor.close()
        connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)