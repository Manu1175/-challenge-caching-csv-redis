import redis
import sys
import time
import logging
from datetime import timedelta
import pandas as pd
from dotenv import load_dotenv
import os
from logging.handlers import RotatingFileHandler

# Load .env variables
load_dotenv()

# ---------------------------
# Configure logging
# ---------------------------

logger = logging.getLogger(__name__)  # DO NOT configure handlers here

class RedisCache:
    def __init__(self):
        """Establish connection with Redis."""
        REDIS_HOST = os.getenv("REDIS_HOST")
        REDIS_PORT = int(os.getenv("REDIS_PORT"))
        REDIS_DB = int(os.getenv("REDIS_DB"))

        try:
            client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            if client.ping():
                self.client = client
                logging.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}, db={REDIS_DB}")
            else:
                logging.warning("Connection established but Redis did not respond to ping!")
                sys.exit(1)
        except redis.ConnectionError as ex:
            logging.error(f"Redis Connection Error: {ex}")
            sys.exit(1)

    def set_cached(self, query: str, result: dict, CACHE_TTL: int = 900): #seconds
        """
        Store result in Redis as a hash with TTL.
        """
        cache_key = f"cache:{query}"
        # Store dictionary as a Redis hash
        self.client.hset(cache_key, mapping={str(k): str(v) for k, v in result.items()})
        # Set TTL
        self.client.expire(cache_key, CACHE_TTL)
        logging.info(f"Cached result for query '{query}' as HASH with TTL={CACHE_TTL}s")

    def get_cached(self, query: str):
        """
        Retrieve result from Redis hash.
        """
        cache_key = f"cache:{query}"
        start = time.time()
        if self.client.exists(cache_key):
            # Get all fields from the hash
            cached = self.client.hgetall(cache_key)
            elapsed = round((time.time() - start) * 1000, 2)  # ms
            ttl = self.client.ttl(cache_key)
            # Convert values back to float if possible
            result = {
                k: float(v) if v.replace('.', '', 1).isdigit() else v
                for k, v in cached.items()
            }
            logging.info(f"Cache HIT for query '{query}' (elapsed={elapsed}ms, TTL={ttl}s)")
            return result
        elapsed = round((time.time() - start) * 1000, 2)
        logging.info(f"Cache MISS for query '{query}' (checked in {elapsed}ms)")
        return None

    def get_single_value(self, query: str, field: str):
        """
        Retrieve a single value (field) from a cached Redis hash.
        """
        cache_key = f"cache:{query}"
        field = str(field).strip()   # normalize lookup
        start = time.time()
        if self.client.hexists(cache_key, field):
            value = self.client.hget(cache_key, field)
            elapsed = round((time.time() - start) * 1000, 2)
            ttl = self.client.ttl(cache_key)
            try:
                value = float(value)
            except ValueError:
                pass
            logging.info(f"Cache HIT for query '{query}', field '{field}' "
                        f"(elapsed={elapsed}ms, TTL={ttl}s)")
            return value
        else:
            logging.info(f"Cache MISS for query '{query}', field '{field}'")
            return None

    def compute_aggregation(self, group_by: str, column: str, agg_func: str, csv_file: str = "data/flights.csv"):
        """
        Compute aggregation on a flights CSV file.

        group_by: column to group by (e.g., AIRLINE, ORIGIN_AIRPORT)
        column: column to aggregate (e.g., ARRIVAL_DELAY, CANCELLED)
        agg_func: aggregation function ('mean', 'max', 'min', 'std', 'sum', 'count')
        csv_file: path to the CSV file (default: 'data/flights.csv')
        """
        query = f"{agg_func}_{column}_per_{group_by}"

        # Try Redis cache first
        cached_result = self.get_cached(query)
        if cached_result:
            return cached_result

        # Load CSV inside the method
        start = time.time()
        df = pd.read_csv(csv_file, low_memory=False)

        # Check columns exist
        if group_by not in df.columns or column not in df.columns:
            raise ValueError(f"Columns not found: {group_by}, {column}")

        # Supported aggregation functions
        if agg_func not in ["mean", "min", "max", "std", "sum", "count"]:
            raise ValueError(f"Unsupported aggregation function: {agg_func}")

        # Compute aggregation
        result = getattr(df.groupby(group_by)[column], agg_func)().round(2).to_dict()

        elapsed = round((time.time() - start) * 1000, 2)
        logging.info(f"Computed '{query}' from CSV in {elapsed}ms")

        # Cache the result
        self.set_cached(query, result)

        return result

    def invalidate_cache(self, query: str):
        """
        Invalidate (delete) a specific query cache.
        """
        cache_key = f"cache:{query}"
        if self.client.delete(cache_key):
            logging.info(f"Invalidated cache for query '{query}'")
            return True
        else:
            logging.info(f"No cache found for query '{query}' to invalidate")
            return False

    def clear_all_cache(self, prefix: str = "cache:*"):
        """
        Clear all cached queries matching the prefix (default: all flight caches).
        """
        keys = self.client.keys(prefix)
        if keys:
            self.client.delete(*keys)
            logging.info(f"Cleared {len(keys)} cached queries (prefix='{prefix}')")
            return len(keys)
        logging.info(f"No cached queries found for prefix='{prefix}'")
        return 0
