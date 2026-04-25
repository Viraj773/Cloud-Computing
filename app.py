from flask import Flask, render_template, request, redirect, url_for, session
import boto3
from boto3.dynamodb.conditions import Key

app = Flask(__name__)
app.secret_key = 'musicapp2026'

# AWS credentials - update these every time you start the lab
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id='ASIAVKS35N6MCSAFBUW6',
    aws_secret_access_key='lQIjuR57anw+1Wb+CJdILOzKUB74aY9Q2uIn/O3c',
    aws_session_token='IQoJb3JpZ2luX2VjEM7//////////wEaCXVzLXdlc3QtMiJIMEYCIQDUpWs3j7mGHjlLqXkZP3DE27B/Hp/4VJbdzjzK+EBeowIhAJgyv4xey31tV1zwsJosiwldqDuO9AHXNqfKgvtwlY5IKr8CCJf//////////wEQBBoMMzY2MzM4NzMxOTI4IgwFf0s3/iB8wzvra9EqkwK9Bv0GDGAR3WUuWQ5iW1WQGowEZ4hmwHQqbnQ3KtceZQEwH1m4/Q/bPHvKMV6D718Pniq+f0eU3G8ktbOIEbromrBugybhag1KMWOJ8tGdt0Fun4tsPuRIihJir33bnHEelW6rRkwofwpK8Rx2EouNoAX12pODUE7rLCT2oVTy2fMbb9Y0uly+Q8DmsUfRn4jGSDw1L7Wk/dl0tg29g9BrqIIWnWhyVwvW7r7JdsAsJ5ZG7mPkiKNQSej+6d7qCtB7l+TCbWanWL1/+7swlJMjnhxkFJTyCqU8szPwNBrWgYB0dRtGJ8MsJCZYj7Ud8wcGVt2XHhglbbG01GS7Uglt83IVIkEjLVQy8Nf2ZIujlDpW2jCehLPPBjqcARC3zc9N2FWHnOOgnFh+7myFI7s9Pykh1eNCDVj/i+6L1ZzST90vcmC1SfdS/f3QASTlgTBYLNF6IYPzfSGE8ehRZxXitaLiqM2jEuD0pfI7ot95f396eED/livwPwHXfXrKpNYB89NN8NHGvVHHrfoPln65b1XR/gRt5mBc3rDBxa/HXv2Hl6qbWx06G+kEGLD2keeDKLVZ0HKB+Q=='
)

s3 = boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id='ASIAVKS35N6MCSAFBUW6',
    aws_secret_access_key='lQIjuR57anw+1Wb+CJdILOzKUB74aY9Q2uIn/O3c',
    aws_session_token='IQoJb3JpZ2luX2VjEM7//////////wEaCXVzLXdlc3QtMiJIMEYCIQDUpWs3j7mGHjlLqXkZP3DE27B/Hp/4VJbdzjzK+EBeowIhAJgyv4xey31tV1zwsJosiwldqDuO9AHXNqfKgvtwlY5IKr8CCJf//////////wEQBBoMMzY2MzM4NzMxOTI4IgwFf0s3/iB8wzvra9EqkwK9Bv0GDGAR3WUuWQ5iW1WQGowEZ4hmwHQqbnQ3KtceZQEwH1m4/Q/bPHvKMV6D718Pniq+f0eU3G8ktbOIEbromrBugybhag1KMWOJ8tGdt0Fun4tsPuRIihJir33bnHEelW6rRkwofwpK8Rx2EouNoAX12pODUE7rLCT2oVTy2fMbb9Y0uly+Q8DmsUfRn4jGSDw1L7Wk/dl0tg29g9BrqIIWnWhyVwvW7r7JdsAsJ5ZG7mPkiKNQSej+6d7qCtB7l+TCbWanWL1/+7swlJMjnhxkFJTyCqU8szPwNBrWgYB0dRtGJ8MsJCZYj7Ud8wcGVt2XHhglbbG01GS7Uglt83IVIkEjLVQy8Nf2ZIujlDpW2jCehLPPBjqcARC3zc9N2FWHnOOgnFh+7myFI7s9Pykh1eNCDVj/i+6L1ZzST90vcmC1SfdS/f3QASTlgTBYLNF6IYPzfSGE8ehRZxXitaLiqM2jEuD0pfI7ot95f396eED/livwPwHXfXrKpNYB89NN8NHGvVHHrfoPln65b1XR/gRt5mBc3rDBxa/HXv2Hl6qbWx06G+kEGLD2keeDKLVZ0HKB+Q=='
)

BUCKET_NAME = 's4078067-mybucket'

# HELPER FUNCTION

def get_image_url(img_url):
    img_filename = img_url.split('/')[-1]
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': BUCKET_NAME,
            'Key': img_filename
        },
        ExpiresIn=3600
    )
    return url


# CREATE SUBSCRIPTIONS TABLE

def create_subscriptions_table():
    try:
        table = dynamodb.create_table(
            TableName='subscriptions',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'},
                {'AttributeName': 'title', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'title', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='subscriptions')
        print("Subscriptions table created!")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("Subscriptions table already exists.")
        else:
            print(f"Error: {e}")

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
        response = table.get_item(Key={'email': email})
        user = response.get('Item')

        if user:
            error = 'The email already exists'
        else:
            table.put_item(
                Item={
                    'email': email,
                    'user_name': username,
                    'password': password
                }
            )
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

# MAIN PAGE

@app.route('/main')
def main():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # Get user's subscriptions
    sub_table = dynamodb.Table('subscriptions')
    response = sub_table.query(
        KeyConditionExpression=Key('email').eq(session['email'])
    )
    subscriptions = response.get('Items', [])

    # Generate pre-signed URLs for subscription images
    for song in subscriptions:
        if 'img_url' in song:
            song['presigned_url'] = get_image_url(song['img_url'])
    
    return render_template('main.html', 
                         username=session['username'],
                         subscriptions=subscriptions,
                         query_results=None)

# QUERY SONGS

@app.route('/query', methods=['POST'])
def query():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    title = request.form.get('title', '').strip()
    artist = request.form.get('artist', '').strip()
    year = request.form.get('year', '').strip()
    album = request.form.get('album', '').strip()
    
    music_table = dynamodb.Table('music')
    filter_expression = []
    expression_values = {}
    expression_names = {}

    if title:
        filter_expression.append('#t = :title')
        expression_values[':title'] = title
        expression_names['#t'] = 'title'
    if artist:
        filter_expression.append('#a = :artist')
        expression_values[':artist'] = artist
        expression_names['#a'] = 'artist'
    if year:
        filter_expression.append('#y = :year')
        expression_values[':year'] = year
        expression_names['#y'] = 'year'
    if album:
        filter_expression.append('#al = :album')
        expression_values[':album'] = album
        expression_names['#al'] = 'album'

    if not filter_expression:
        return redirect(url_for('main'))

    response = music_table.scan(
        FilterExpression=' AND '.join(filter_expression),
        ExpressionAttributeValues=expression_values,
        ExpressionAttributeNames=expression_names
    )
    query_results = response.get('Items', [])

    # Generate pre-signed URLs for query results
    # Keep original img_url, store presigned in separate field
    for song in query_results:
        if 'img_url' in song:
            song['presigned_url'] = get_image_url(song['img_url'])

    # Get subscriptions
    sub_table = dynamodb.Table('subscriptions')
    sub_response = sub_table.query(
        KeyConditionExpression=Key('email').eq(session['email'])
    )
    subscriptions = sub_response.get('Items', [])

    # Generate pre-signed URLs for subscriptions
    for song in subscriptions:
        if 'img_url' in song:
            song['presigned_url'] = get_image_url(song['img_url'])

    return render_template('main.html',
                         username=session['username'],
                         subscriptions=subscriptions,
                         query_results=query_results)

# SUBSCRIBE TO A SONG

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    sub_table = dynamodb.Table('subscriptions')
    sub_table.put_item(
        Item={
            'email': session['email'],
            'title': request.form['title'],
            'artist': request.form['artist'],
            'year': request.form['year'],
            'album': request.form['album'],
            'img_url': request.form['img_url']  # saves original URL
        }
    )
    return redirect(url_for('main'))

# REMOVE SUBSCRIPTION

@app.route('/remove', methods=['POST'])
def remove():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    sub_table = dynamodb.Table('subscriptions')
    sub_table.delete_item(
        Key={
            'email': session['email'],
            'title': request.form['title']
        }
    )
    return redirect(url_for('main'))

# LOGOUT

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_subscriptions_table()
    app.run(debug=True)