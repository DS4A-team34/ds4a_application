import os
from dotenv import load_dotenv

load_dotenv()


DATABASE = {
    'USER': os.getenv('DATABASE_USER'),
    'HOST': os.getenv('DATABASE_HOST'),
    'NAME': os.getenv('DATABASE_NAME'),
}
# compute database string connection
DATABASE['CONNECTION'] = f"postgresql://{DATABASE['USER']}:{DATABASE['HOST']}/{DATABASE['NAME']}"
