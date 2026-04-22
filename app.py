from flask import Flask, render_template, request, redirect, url_for, session
import boto3
app = Flask(__name__)
app.secret_key = 'musicapp2026'

# AWS credentials - update these every time you start the lab
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id='ASIAVKS35N6MD6LA374J',
    aws_secret_access_key='jlqlXmby5n0F0+t7FOx1Isvtav+32LsNpViA0UuW',
    aws_session_token='IQoJb3JpZ2luX2VjEIf//////////wEaCXVzLXdlc3QtMiJHMEUCIQCwsZOK02ZaLth0Pzad4ZTBT0cQf0hpEzDwPLeqnP9EigIgVhQDIxRGEgN4km+xn5aWJBxBwy0mcaGSMSSPvBnkLiMqtgIIUBAEGgwzNjYzMzg3MzE5MjgiDI7+4zYNFWW3T6e4MiqTAirmeAYBmczFxMI2otCLJbxXpgogcOZwh4LIdYyG/qArSgFJpkgMHYloC4FitPpEkE8zHj5AOkLo0dW531t+0E4nf6YgFhSRnAmkgJnuBvXcgTpvSxOBlLiqKocVxsuRwGtCqYNhFaBEmr6z9yCTyBzvr2K41XsPh9NMwyCf0Qy5AE3s56qt6V/C/tn5E8M4e3T/w2aoshWRX7pEBc7ugWEC+ZMJjsG2fDvKScF9EY4289waF4EZGvfBiRED9hdqvJYLyP6f3o1vAdcnbhhRw+8c7ZtZa1d7nNGvwRhruHThRwUVxlJojBCbNlTqWwkhZb7boI/0iBHbdUf3b85p3cQYtdlJs4t778TQpB8rFKTZhyH4MN7Co88GOp0BrRexvytmwLNxnEnBUsq1H04tLKNEmNejRA0HfalgdScNN1xnTi/gSpVnQiJqNE3IvlnFH+oAFoRtM2t5Zrayi6LeyuffIFFgzckjktcjId6XXLp64Wlead/aH8cP3jihgO6bH45LW3nrxrA62wxecOUGNAF+dMhTR3L3qpqAi198DWOEw0LeK2Y7ve4W1AOY3ZlDWYT1tIIqOU+bJQ=='
)

# LOGIN PAGE

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        table = dynamodb.Table('login')
        response = table.get_item(Key={'email': email})
        user = response.get('Item')
        
        if user and user['password'] == password:
            session['email'] = email
            session['username'] = user['user_name']
            return redirect(url_for('main'))
        else:
            error = 'email or password is invalid'
    
    return render_template('login.html', error=error)

# REGISTER PAGE

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        table = dynamodb.Table('login')

        # Check if email already exists
        response = table.get_item(Key={'email': email})
        user = response.get('Item')

        if user:
            error = 'The email already exists'
        else:
            # Save new user to DynamoDB
            table.put_item(
                Item={
                    'email': email,
                    'user_name': username,
                    'password': password
                }
            )
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

# MAIN PAGE (temporary)
@app.route('/main')
def main():
    if 'email' not in session:
        return redirect(url_for('login'))
    return f"Welcome {session['username']}! Main page coming soon..."

# LOGOUT

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)