import os
import redis
from werkzeug.utils import import_string

class Config:
    # App Secret Key
    SECRET_KEY = os.environ.get("SECRET_KEY", "sXMqeur05zwperRDT7fEQianVp3azxVafDDosSLGqsU")

    # REDIS
    redis_endpoint_url = os.environ.get("REDIS_ENDPOINT_URL", "localhost:16379")
    REDIS_PASSWORD     = os.environ.get("REDIS_PASSWORD", 'redis123')
    REDIS_HOST, REDIS_PORT = tuple(redis_endpoint_url.split(":"))
    SESSION_TYPE = "redis"
    redis_client = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD
    )
    SESSION_REDIS = redis_client

class ConfigDev(Config):
    DEBUG = True

class ConfigProd(Config):
    DEBUG = False

def get_config() -> Config:
    return import_string(os.environ.get("CHAT_CONFIG", "app.config.ConfigDev"))

