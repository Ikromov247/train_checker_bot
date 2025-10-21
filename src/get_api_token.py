import dotenv
import os
from pathlib import Path

current_dir = Path(__file__).resolve().parent
dotenv_path = current_dir.parent / '.env'
dotenv.load_dotenv(dotenv_path=dotenv_path)

token = os.environ.get("API_TOKEN", None) 

def get_api_token():
    return token