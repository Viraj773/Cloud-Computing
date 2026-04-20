from flask import Flask, render_template, request, redirect, url_for, session
import boto3

app=Flask(__name__)
app.secret_key='musicapp2026' #Needed for session management

#AWS credentials- Needs to be updated every time you start lab
dynamodb =boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id='ASIAVKS35N6MGGVTVTK2',
    aws_secret_access_key='qJ8vT9vFw3Nqyk0SYw/GPDJXRvVnHnjKMfVZxjoN',
    aws_session_token='IQoJb3JpZ2luX2VjEFcaCXVzLXdlc3QtMiJGMEQCIB1gQi+V2fhU1RuvpcBp4/QOQyByRQNX+jzBMdgc6UzaAiAXOrPGnlGgwLeaVmaq7xIyzspne7+rBclVouPnwRRL0Sq2AgggEAQaDDM2NjMzODczMTkyOCIM4fFolHygcWrRRsd6KpMCwc1vynLwpCKbuZ27BGvubjcMpQcMwpoOEAVKqaUzFGU5s6CvxVoZ7ksWhOm0oGX7yQmXN7AX4qqwcnfZubYSMnU9MbwVzHGw1MmALXP5jBl+Mapwl/tzt5bZXN0hXXYjaLlBG/OmThpXMe+gpPd2GkMJkg7SkUBAz4kz5ipY0+rX6SUMovE4YwDwSnBpolv1QEhUwPkvF3fT3EgMU5HErhDuBfEsm3T7BDHXcCqKGOqP3OyfbT6GwCyQ99yJc2l5/ejmUgpoBweMKxM3qWmlMcJecHZ7nhfJQ1iM2bm9Fd05budU2RSyjNLIxUAalm27M4T5qThRNb9oA1B/4aP11Mp3k7cnq05tBRQiqVnqJ3PSOcUwpPeYzwY6ngEyPpvAlzkI1Db45wX2Ka+Se/rstJ1PMfKCbg7wc5NbV5wvUq+R+SdTxjfgkuIB7Io4kP27i0qfjIwsoYdXKLLJYtI2qBtEdNYJcPdImLXl8CyePQmGKNRTr4w128kmPppv9KvZdSjDunpZvcjYwHOUqYNTLevMH8aXx/msEo6B9CTEHni0c52Zh3/Gz9jetZeDoZpBpIt49XaXVhzU8Q==',
)

# =====================
# LOGIN PAGE
# =====================
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

# =====================
# LOGOUT
# =====================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/main')
def main():
    if 'email' not in session:
        return redirect(url_for('login'))
    return f"Welcome {session['username']}! Main page coming soon..."

if __name__ == '__main__':
    app.run(debug=True)