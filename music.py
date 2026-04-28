import json
from io import BytesIO

import boto3
import requests
from botocore.exceptions import ClientError

REGION_NAME = "us-east-1"

AWS_ACCESS_KEY_ID = "PASTE_ACCESS_KEY_HERE"
AWS_SECRET_ACCESS_KEY = "PASTE_SECRET_KEY_HERE"
AWS_SESSION_TOKEN = "PASTE_SESSION_TOKEN_HERE"


def using_placeholder_credentials():
    return (
        AWS_ACCESS_KEY_ID == "PASTE_ACCESS_KEY_HERE"
        or AWS_SECRET_ACCESS_KEY == "PASTE_SECRET_KEY_HERE"
        or AWS_SESSION_TOKEN == "PASTE_SESSION_TOKEN_HERE"
    )


if using_placeholder_credentials():
    # On EC2 boto3 automatically uses LabInstanceProfile/LabRole
    dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
    s3 = boto3.client("s3", region_name=REGION_NAME)
else:
    # For local testing we can paste the temporary AWS academy credentials above
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

    s3 = boto3.client(
        "s3",
        region_name=REGION_NAME,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )


# HELPER FUNCTIONS

def make_song_id(song):
    # title + artist was not enough because the dataset has duplicate title/artist pairs
    return f"{song['title']}#{song['album']}#{song['year']}"


def make_s3_key(img_url):
    # Stores images in a clean S3 folder
    filename = img_url.split("/")[-1]
    return f"artist-images/{filename}"


def table_exists(table_name):
    # Checks if a DynamoDB table already exists
    try:
        dynamodb.meta.client.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


# LOGIN TABLE

def create_login_table():
    try:
        if table_exists(LOGIN_TABLE):
            print(f"{LOGIN_TABLE} table already exists. Skipping creation.")
            return

        print(f"Creating {LOGIN_TABLE} table...")

        login_tab = dynamodb.create_table(
            TableName=LOGIN_TABLE,
            KeySchema=[
                {"AttributeName": "email", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        login_tab.meta.client.get_waiter("table_exists").wait(TableName=LOGIN_TABLE)
        print("Login table created successfully.")

    except Exception as e:
        print(f"Error creating login table: {e}")


def login_data():
    # Adds the 10 required login users
    l_table = dynamodb.Table(LOGIN_TABLE)

    student_id = "s4087536"
    student_name = "MaitreyaKadam"

    try:
        with l_table.batch_writer() as batch:
            for i in range(10):
                email = f"{student_id}{i}@student.rmit.edu.au"
                user_name = f"{student_name}{i}"
                password = "".join(str((i + j) % 10) for j in range(6))

                batch.put_item(
                    Item={
                        "email": email,
                        "user_name": user_name,
                        "password": password
                    }
                )

        print("Added 10 users to login table.")

    except Exception as e:
        print(f"Error adding login data: {e}")


# MUSIC TABLE

def music_table():
    try:
        if table_exists(MUSIC_TABLE):
            print(f"{MUSIC_TABLE} table already exists. Skipping creation.")
            print("If it uses the old title + artist schema, delete it and rerun this script.")
            return

        print(f"Creating {MUSIC_TABLE} table...")

        music_tab = dynamodb.create_table(
            TableName=MUSIC_TABLE,
            KeySchema=[
                {"AttributeName": "artist", "KeyType": "HASH"},
                {"AttributeName": "song_id", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "artist", "AttributeType": "S"},
                {"AttributeName": "song_id", "AttributeType": "S"},
                {"AttributeName": "album", "AttributeType": "S"},
                {"AttributeName": "title", "AttributeType": "S"},
                {"AttributeName": "year", "AttributeType": "S"}
            ],
            LocalSecondaryIndexes=[
                {
                    "IndexName": "artist-album-index",
                    "KeySchema": [
                        {"AttributeName": "artist", "KeyType": "HASH"},
                        {"AttributeName": "album", "KeyType": "RANGE"}
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"
                    }
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "title-year-index",
                    "KeySchema": [
                        {"AttributeName": "title", "KeyType": "HASH"},
                        {"AttributeName": "year", "KeyType": "RANGE"}
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"
                    }
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        music_tab.meta.client.get_waiter("table_exists").wait(TableName=MUSIC_TABLE)
        print("Music table created with PK artist, SK song_id, one LSI and one GSI.")

    except Exception as e:
        print(f"Error creating music table: {e}")


def music_data(f_name):
    # Loads all 137 songs without dropping duplicate title/artist songs
    m_table = dynamodb.Table(MUSIC_TABLE)

    try:
        with open(f_name, "r", encoding="utf-8") as f:
            m_data = json.load(f)
            song_l = m_data["songs"]

        print(f"Loading {len(song_l)} songs...")

        unique_keys = set()

        with m_table.batch_writer() as batch:
            for e_song in song_l:
                song_id = make_song_id(e_song)
                s3_key = make_s3_key(e_song["img_url"])

                unique_key = (e_song["artist"], song_id)

                if unique_key in unique_keys:
                    raise ValueError(f"Duplicate generated key found: {unique_key}")

                unique_keys.add(unique_key)

                batch.put_item(
                    Item={
                        "artist": e_song["artist"],
                        "song_id": song_id,
                        "title": e_song["title"],
                        "year": str(e_song["year"]),
                        "album": e_song["album"],
                        "img_url": e_song["img_url"],
                        "s3_key": s3_key
                    }
                )

        print(f"Loaded {len(unique_keys)} songs into the music table.")

    except Exception as e:
        print(f"An error has occurred while loading music data: {e}")


# SUBSCRIPTIONS TABLE

def create_subscriptions_table():
    try:
        if table_exists(SUBSCRIPTIONS_TABLE):
            print(f"{SUBSCRIPTIONS_TABLE} table already exists. Skipping creation.")
            print("If it uses email + title, delete it and rerun this script.")
            return

        print(f"Creating {SUBSCRIPTIONS_TABLE} table...")

        sub_tab = dynamodb.create_table(
            TableName=SUBSCRIPTIONS_TABLE,
            KeySchema=[
                {"AttributeName": "email", "KeyType": "HASH"},
                {"AttributeName": "song_id", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"},
                {"AttributeName": "song_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        sub_tab.meta.client.get_waiter("table_exists").wait(TableName=SUBSCRIPTIONS_TABLE)
        print("Subscriptions table created successfully.")

    except Exception as e:
        print(f"Error creating subscriptions table: {e}")


# S3 BUCKET AND IMAGES

def initialize_s3bucket():
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print("S3 bucket created.")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "BucketAlreadyOwnedByYou":
            print("Bucket already exists.")
        elif error_code == "BucketAlreadyExists":
            print("Bucket name is already taken by someone else.")
        else:
            print(f"Error creating S3 bucket: {e}")


def download_img(f_name):
    # Downloads each unique artist image and uploads it to S3
    try:
        with open(f_name, "r", encoding="utf-8") as f:
            m_data = json.load(f)
            song_l = m_data["songs"]

        downloaded_imgurls = set()

        for e_song in song_l:
            image = e_song.get("img_url")

            if not image or image in downloaded_imgurls:
                continue

            s3_key = make_s3_key(image)

            try:
                response = requests.get(image, timeout=15)
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "image/jpeg")

                s3.upload_fileobj(
                    BytesIO(response.content),
                    BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        "ContentType": content_type
                    }
                )

                downloaded_imgurls.add(image)
                print(f"Uploaded {s3_key}")

            except Exception as de:
                print(f"Error processing image {image}: {de}")

        print(f"Uploaded {len(downloaded_imgurls)} unique artist images to S3.")

    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"Error: {e}")


# DATASET CHECK

def analyse_dataset(f_name):
    # Shows why title + artist was not enough as a key
    try:
        with open(f_name, "r", encoding="utf-8") as f:
            songs = json.load(f)["songs"]

        total = len(songs)
        unique_title_artist = len(set((s["title"], s["artist"]) for s in songs))
        unique_full_identity = len(set((s["title"], s["artist"], s["album"], s["year"]) for s in songs))

        print("Dataset analysis:")
        print(f"Total songs: {total}")
        print(f"Unique title + artist pairs: {unique_title_artist}")
        print(f"Unique title + artist + album + year records: {unique_full_identity}")

        if total != unique_title_artist:
            print("title + artist is not unique enough. Using artist + song_id instead.")

    except Exception as e:
        print(f"Error analysing dataset: {e}")


if __name__ == "__main__":
    analyse_dataset(SONGS_FILE)
    create_login_table()
    login_data()
    music_table()
    music_data(SONGS_FILE)
    create_subscriptions_table()
    initialize_s3bucket()
    download_img(SONGS_FILE)
    print("Initialisation complete.")