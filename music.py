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
    aws_access_key_id='ASIAVKS35N6MFIVSXQ4I',          #change this when starting the lab
    aws_secret_access_key='5kFmpRvaOqa5S1ngKx/5kDN+IYrt/uZPXspK4CBq',  #change this when starting the lab
    aws_session_token='IQoJb3JpZ2luX2VjEE0aCXVzLXdlc3QtMiJHMEUCIQDTkCtUk9pHfMsPatY1OjJLcITnnEmVP1H5+Cd8NJIb9QIgGnPqz+Xy/YgAcPbs46sThH5juOyi61aUQkdkVn0622UqtgIIFhAEGgwzNjYzMzg3MzE5MjgiDIUgYYFuQJ3H+VTKwCqTAtPEeqz1Lu1qqP9xbKpi/YYg4Uz2cjHVZyBv8Nes34vFEd/yqhOuGdIndaelElRwa+8t+b892dtLp2TVXiJhJmjCDXc9jGHdaP1IJR/hFO13A2jWXiOyLbuBgXQtm5hi0wvA8cYYWNuoQ3Z3tiYRjWleSPVYqBDtjIW1s1SPyXqOUPdt/xp4goImmeWGCxgHkvS4IuMHM1v2CVAaHWgdLGS/n2s3Vow8L+t5tYChEMsWlorW8mJcyqveTBvytLHGMsVc6CkMvlW2g3PQLuSxA2Op4qeE5A5VJ1XeTwrdmI9Nr4h/r3SiYGHUe6x5a640fU0e7VotSd4C5ehhiSyKCN8PpYgDXVFXUu59TQSr6RT/xaOdMJzals8GOp0B2grS5Cq7t1x0vOIeq/EuuSW1zW+2MRY3w1hXfZB7JSo2HwRVnqPtl+sOYbMddsQ6cyIf+4dDFEu4fs4+OfqkiucWGMA82UMPdrqvUdRPaiyAkqErq9RbDq8oXOZeDZyI3I7mOCbqqV/zeJEYRapd8/3wOQWlKgmooXhCuob+MqT51ucWC0wQPfdVzRtachahn9SgjPS0JumTpk4l2w==' #change this when starting the lab
)

s3=boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id='ASIAVKS35N6MFIVSXQ4I', #Change this when starting the lab
    aws_secret_access_key='5kFmpRvaOqa5S1ngKx/5kDN+IYrt/uZPXspK4CBq', #change this when starting the AWS lab
    aws_session_token='IQoJb3JpZ2luX2VjEE0aCXVzLXdlc3QtMiJHMEUCIQDTkCtUk9pHfMsPatY1OjJLcITnnEmVP1H5+Cd8NJIb9QIgGnPqz+Xy/YgAcPbs46sThH5juOyi61aUQkdkVn0622UqtgIIFhAEGgwzNjYzMzg3MzE5MjgiDIUgYYFuQJ3H+VTKwCqTAtPEeqz1Lu1qqP9xbKpi/YYg4Uz2cjHVZyBv8Nes34vFEd/yqhOuGdIndaelElRwa+8t+b892dtLp2TVXiJhJmjCDXc9jGHdaP1IJR/hFO13A2jWXiOyLbuBgXQtm5hi0wvA8cYYWNuoQ3Z3tiYRjWleSPVYqBDtjIW1s1SPyXqOUPdt/xp4goImmeWGCxgHkvS4IuMHM1v2CVAaHWgdLGS/n2s3Vow8L+t5tYChEMsWlorW8mJcyqveTBvytLHGMsVc6CkMvlW2g3PQLuSxA2Op4qeE5A5VJ1XeTwrdmI9Nr4h/r3SiYGHUe6x5a640fU0e7VotSd4C5ehhiSyKCN8PpYgDXVFXUu59TQSr6RT/xaOdMJzals8GOp0B2grS5Cq7t1x0vOIeq/EuuSW1zW+2MRY3w1hXfZB7JSo2HwRVnqPtl+sOYbMddsQ6cyIf+4dDFEu4fs4+OfqkiucWGMA82UMPdrqvUdRPaiyAkqErq9RbDq8oXOZeDZyI3I7mOCbqqV/zeJEYRapd8/3wOQWlKgmooXhCuob+MqT51ucWC0wQPfdVzRtachahn9SgjPS0JumTpk4l2w=='
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
