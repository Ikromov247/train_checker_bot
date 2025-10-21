import dotenv
import os

dotenv.load_dotenv()
tokens = os.environ.get("API_TOKEN", None) 

def get_api_token()->str:
    return token