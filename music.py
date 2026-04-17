import boto3
import json
import requests
from io import BytesIO
from botocore.exceptions import ClientError



BUCKET_NAME='s4087536-mybucket'  #change this according to your student no for testing purposes

# change the port no in endpoint url acc to your terminal
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    #endpoint_url='http://localhost:8000', # local port no on LM
    aws_access_key_id='ASIAWW2CU32B2E5ZAEEJ',          #change this when starting the lab
    aws_secret_access_key='J7pCG0ilNOVexOXUwO/D9a4hqWVqpiuzfcOkjOTf',  #change this when starting the lab
    aws_session_token='IQoJb3JpZ2luX2VjEAUaCXVzLXdlc3QtMiJHMEUCIDkehpAncNunc28Ooj7EUtYS7EA9nEgpUhsW+YUam4YQAiEA4UtJPsD8iVH7d2UAhIXSm2PlgC3S9yT9Pd3SiWFGc2YqvwIIzv//////////ARABGgw0NjEzMTE4OTMxMjMiDJXVm5gora2LNLcWcCqTAmzYNJLb1SUMZrP5+j8XquCe6d215Brmyr+4gVbvuRymKlSh0Ow8x7/rQr0jLcUt/pZwF8NrdauedhyCEN1D/h+8k2HWiltxuePL7aDsJdFJVjHxN7lB3fYnoiowX3AJmV/1EMgVNAjL3lmJr59ECc4/jqWhOiMLoS64vxjqsJm0WjecvZN3tzGWixlkJYxfWXZYHI6HYKp64ocutT0+EHQIDDcy0iM5+LCJGwjI84Aa8/1WPwifgA3AiWSPCfSDEd4Sxoj5LuTE4emnzMgiy6EBQoLv3dwNovKjOrbDduNRAIJvrz1AnuYUC6Yw0o7YYHNg8lIdt+0k27mNZWecYZL+L2RRdTT0bo8mgsLFdeZQKhGbMOn9hs8GOp0BfJw/La6KYJxSNgQSKRsECvc/FCyK6+OXY2kyhgPmtmg106uw7QqEusa+C2C7rtJvr/Kso/qk+oKS1774qRgrP8wWh3KX0ighjI4mc9AZF6Z/M5r59lP0faRSYXuPSNiFzOUEJ3r604966r8GKk/dOhXrCvRhZGmTk4OE9OCNbfdHNIECcKIlwy1NZ5v5CDTvlsousuCOEsG8RKGFDQ==' #change this when starting the lab
)

s3=boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id='ASIAWW2CU32B2E5ZAEEJ', #Change this when starting the lab
    aws_secret_access_key='J7pCG0ilNOVexOXUwO/D9a4hqWVqpiuzfcOkjOTf', #change this when starting the AWS lab
    aws_session_token='IQoJb3JpZ2luX2VjEAUaCXVzLXdlc3QtMiJHMEUCIDkehpAncNunc28Ooj7EUtYS7EA9nEgpUhsW+YUam4YQAiEA4UtJPsD8iVH7d2UAhIXSm2PlgC3S9yT9Pd3SiWFGc2YqvwIIzv//////////ARABGgw0NjEzMTE4OTMxMjMiDJXVm5gora2LNLcWcCqTAmzYNJLb1SUMZrP5+j8XquCe6d215Brmyr+4gVbvuRymKlSh0Ow8x7/rQr0jLcUt/pZwF8NrdauedhyCEN1D/h+8k2HWiltxuePL7aDsJdFJVjHxN7lB3fYnoiowX3AJmV/1EMgVNAjL3lmJr59ECc4/jqWhOiMLoS64vxjqsJm0WjecvZN3tzGWixlkJYxfWXZYHI6HYKp64ocutT0+EHQIDDcy0iM5+LCJGwjI84Aa8/1WPwifgA3AiWSPCfSDEd4Sxoj5LuTE4emnzMgiy6EBQoLv3dwNovKjOrbDduNRAIJvrz1AnuYUC6Yw0o7YYHNg8lIdt+0k27mNZWecYZL+L2RRdTT0bo8mgsLFdeZQKhGbMOn9hs8GOp0BfJw/La6KYJxSNgQSKRsECvc/FCyK6+OXY2kyhgPmtmg106uw7QqEusa+C2C7rtJvr/Kso/qk+oKS1774qRgrP8wWh3KX0ighjI4mc9AZF6Z/M5r59lP0faRSYXuPSNiFzOUEJ3r604966r8GKk/dOhXrCvRhZGmTk4OE9OCNbfdHNIECcKIlwy1NZ5v5CDTvlsousuCOEsG8RKGFDQ=='
    #change the above when starting the lab
)

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
