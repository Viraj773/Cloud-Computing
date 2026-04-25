import boto3
import json
import requests
from io import BytesIO
from botocore.exceptions import ClientError



BUCKET_NAME='s4078067-mybucket'  #change this according to your student no for testing purposes

# change the port no in endpoint url acc to your terminal
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    #endpoint_url='http://localhost:8000', # local port no on LM
    aws_access_key_id='ASIAVKS35N6MCSAFBUW6',          #change this when starting the lab
    aws_secret_access_key='lQIjuR57anw+1Wb+CJdILOzKUB74aY9Q2uIn/O3c',  #change this when starting the lab
    aws_session_token='IQoJb3JpZ2luX2VjEM7//////////wEaCXVzLXdlc3QtMiJIMEYCIQDUpWs3j7mGHjlLqXkZP3DE27B/Hp/4VJbdzjzK+EBeowIhAJgyv4xey31tV1zwsJosiwldqDuO9AHXNqfKgvtwlY5IKr8CCJf//////////wEQBBoMMzY2MzM4NzMxOTI4IgwFf0s3/iB8wzvra9EqkwK9Bv0GDGAR3WUuWQ5iW1WQGowEZ4hmwHQqbnQ3KtceZQEwH1m4/Q/bPHvKMV6D718Pniq+f0eU3G8ktbOIEbromrBugybhag1KMWOJ8tGdt0Fun4tsPuRIihJir33bnHEelW6rRkwofwpK8Rx2EouNoAX12pODUE7rLCT2oVTy2fMbb9Y0uly+Q8DmsUfRn4jGSDw1L7Wk/dl0tg29g9BrqIIWnWhyVwvW7r7JdsAsJ5ZG7mPkiKNQSej+6d7qCtB7l+TCbWanWL1/+7swlJMjnhxkFJTyCqU8szPwNBrWgYB0dRtGJ8MsJCZYj7Ud8wcGVt2XHhglbbG01GS7Uglt83IVIkEjLVQy8Nf2ZIujlDpW2jCehLPPBjqcARC3zc9N2FWHnOOgnFh+7myFI7s9Pykh1eNCDVj/i+6L1ZzST90vcmC1SfdS/f3QASTlgTBYLNF6IYPzfSGE8ehRZxXitaLiqM2jEuD0pfI7ot95f396eED/livwPwHXfXrKpNYB89NN8NHGvVHHrfoPln65b1XR/gRt5mBc3rDBxa/HXv2Hl6qbWx06G+kEGLD2keeDKLVZ0HKB+Q==' #change this when starting the lab
)

s3=boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id='ASIAVKS35N6MCSAFBUW6', #Change this when starting the lab
    aws_secret_access_key='lQIjuR57anw+1Wb+CJdILOzKUB74aY9Q2uIn/O3c', #change this when starting the AWS lab
    aws_session_token='IQoJb3JpZ2luX2VjEM7//////////wEaCXVzLXdlc3QtMiJIMEYCIQDUpWs3j7mGHjlLqXkZP3DE27B/Hp/4VJbdzjzK+EBeowIhAJgyv4xey31tV1zwsJosiwldqDuO9AHXNqfKgvtwlY5IKr8CCJf//////////wEQBBoMMzY2MzM4NzMxOTI4IgwFf0s3/iB8wzvra9EqkwK9Bv0GDGAR3WUuWQ5iW1WQGowEZ4hmwHQqbnQ3KtceZQEwH1m4/Q/bPHvKMV6D718Pniq+f0eU3G8ktbOIEbromrBugybhag1KMWOJ8tGdt0Fun4tsPuRIihJir33bnHEelW6rRkwofwpK8Rx2EouNoAX12pODUE7rLCT2oVTy2fMbb9Y0uly+Q8DmsUfRn4jGSDw1L7Wk/dl0tg29g9BrqIIWnWhyVwvW7r7JdsAsJ5ZG7mPkiKNQSej+6d7qCtB7l+TCbWanWL1/+7swlJMjnhxkFJTyCqU8szPwNBrWgYB0dRtGJ8MsJCZYj7Ud8wcGVt2XHhglbbG01GS7Uglt83IVIkEjLVQy8Nf2ZIujlDpW2jCehLPPBjqcARC3zc9N2FWHnOOgnFh+7myFI7s9Pykh1eNCDVj/i+6L1ZzST90vcmC1SfdS/f3QASTlgTBYLNF6IYPzfSGE8ehRZxXitaLiqM2jEuD0pfI7ot95f396eED/livwPwHXfXrKpNYB89NN8NHGvVHHrfoPln65b1XR/gRt5mBc3rDBxa/HXv2Hl6qbWx06G+kEGLD2keeDKLVZ0HKB+Q=='
)

# T1 creates login_table and adds the data into the table in Dynamo DB
def login_table():
    try:
        print('Login Table....') #just for testing on local machine
        login_tab=dynamodb.create_table(
            TableName='login',
            KeySchema=[  #Basically defining the primary key
                {'AttributeName': 'email', 'KeyType': 'HASH'}  # Key Type is the Partition Key
            ],
            AttributeDefinitions=[  #Defines the datatype 
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        login_tab.meta.client.get_waiter('table_exists').wait(TableName='login')
        print("Table created successfully!")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("Table already exists. Skipping creation.")
        else:
            print(f"Error: {e}")

def login_data():
    l_table=dynamodb.Table('login')
    stu_id='s4087536'
    stu_name='MaitreyaKadam'
    try:
        with l_table.batch_writer() as batch:
            for i in range(10):
                email=f"{stu_id}{i}@student.rmit.edu.au"
                user_name=f"{stu_name}{i}"
                password=''.join([str((i+j)%10)for j in range(6)])
                batch.put_item(
                    Item={'email':email,
                          'user_name':user_name,
                          'password':password}
                )
        # print('Added 10 users')
    except Exception as e:
        print(f'Error adding data in login table: {e}')

# T2 creates music table in Dynamo DB
def music_table():
    try:
        print('Music Table Loading...')
        music_tab=dynamodb.create_table(
            TableName='music',
            KeySchema=[
                {'AttributeName': 'title', 'KeyType': 'HASH'},#PK
                {'AttributeName': 'artist', 'KeyType': 'RANGE'} #SK
            ],
            AttributeDefinitions=[
                {'AttributeName': 'title', 'AttributeType': 'S'},
                {'AttributeName': 'artist', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        music_tab.meta.client.get_waiter('table_exists').wait(TableName='music')
        print("Table created successfully!")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("Table already exists. Skipping creation.")
        else:
            print(f"Error: {e}")
  
#T3 reads the json file and adds data to the music table          
def music_data(f_name):
    m_table=dynamodb.Table('music')
    try:
        with open(f_name,'r') as f:
            m_data=json.load(f)
            song_l=m_data['songs']
        print(f'Loading {len(song_l)} songs...')
        music_keys=set()
        u_songs=[]
        duplicates=0
        for e_song in song_l:
            combo=(e_song['title'],e_song['artist'])
            if combo in music_keys:
                duplicates+=1
            else:
                music_keys.add(combo)
                u_songs.append(e_song)
        if duplicates==0:
            print('No duplicates')
        else:
            print(f'Total duplicates found and omitted: {duplicates}')  
        with m_table.batch_writer() as batch:
            for e_song in u_songs:
                batch.put_item(Item=e_song)      
        print(f'Loaded {len(u_songs)} songs into the music table')
    except Exception as e:
        print(f'An error has occurred: {e}')
        
        

# T4 automatically downloads the images from the url and adds them to the S3 bucket which is created.
def initialize_s3bucket():
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
    except ClientError as e:
        if e.response['Error']['Code']=='BucketAlreadyOwnedByYou':
            print('Bucket already exists')
        elif e.response['Error']['Code']=='BucketAlreadyExists':
            print('Bucket name is someone else ')
        else:
            print(f"Error: {e}")

def download_img(f_name):
    try:
        with open(f_name,'r') as f:
            m_data=json.load(f)
            song_l=m_data['songs']
        print('Found Songs')
        downloaded_imgurls=set() #tracking the urls processed
        for e_song in song_l:
            image=e_song.get('img_url') #image url
            if not image or image in downloaded_imgurls:
                continue
            img_fname=image.split('/')[-1]
            try:
                #download the image into streaming memory
                response=requests.get(image,timeout=10)
                if response.status_code==200:
                    s3.upload_fileobj(
                        BytesIO(response.content),
                        BUCKET_NAME,
                        img_fname
                    )
                    downloaded_imgurls.add(image)
                    #print('Uploaded image to S3')
                else:
                    print('Failed to download')
            except Exception as de:
                print(f'Error Processing {image}: {de}')
    except FileNotFoundError:
        print('File not Found')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    login_table()
    login_data()
    music_table()
    music_data('2026a2_songs.json')
    initialize_s3bucket()
    download_img('2026a2_songs.json')
