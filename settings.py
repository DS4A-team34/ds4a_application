import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv('DEBUG')
HOST = os.getenv('HOST')

DATABASE = {
    'USER': os.getenv('DATABASE_USER'),
    'HOST': os.getenv('DATABASE_HOST'),
    'NAME': os.getenv('DATABASE_NAME'),
}
# compute database string connection
DATABASE['CONNECTION'] = f"postgresql://{DATABASE['USER']}:{DATABASE['HOST']}/{DATABASE['NAME']}"

AWS = {
    'ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'REGION_NAME': os.getenv('REGION_NAME'),
    'BUCKET_NAME': os.getenv('BUCKET'),
    'BUCKET_URL': 'https://bootcampaws315.s3.us-east-2.amazonaws.com'
}
