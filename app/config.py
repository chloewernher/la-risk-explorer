import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "LA Urban Environmental Risk Explorer API")
APP_VERSION = os.getenv("APP_VERSION", "0.3.0")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")