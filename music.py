import boto3
import json

# change the port no in endpoint url acc to your terminal
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    endpoint_url='http://localhost:8000', # local port no on LM
    aws_access_key_id='anything',          #these will be changed according to the keys on aws learner lab
    aws_secret_access_key='anything'
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

if __name__ == "__main__":
    login_table()
    login_data()
    music_table()
    music_data('2026a2_songs.json')
