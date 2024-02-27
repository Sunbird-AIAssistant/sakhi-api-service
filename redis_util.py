import redis
import zlib
import pickle
import os
from config_util import get_config_value

# Connect to Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_TTL = get_config_value('redis', 'ttl') # 12 hours (TTL in seconds)
redis_client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=int(REDIS_DB))

def store_messages_in_redis(key, message, ttl=int(REDIS_TTL)):
    """Compresses a message using gzip and stores it in Redis."""
    redis_key = f"msg_{key}"
    serialized_json = pickle.dumps(message)
    compressed_data = zlib.compress(serialized_json)
    redis_client.setex(redis_key, ttl, compressed_data)

def read_messages_from_redis(key):
    """Retrieves a compressed message from Redis and decompresses it."""
    redis_key = f"msg_{key}"
    compressed_data = redis_client.get(redis_key)
    if compressed_data:
        decompressed_data = zlib.decompress(compressed_data)
        return pickle.loads(decompressed_data)
    else:
        return []  # Handle the case where the key doesn't exis
