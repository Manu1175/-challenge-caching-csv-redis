import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from cache import RedisCache

# --- a) Ensure logs folder exists and define absolute path ---
LOG_DIR = "/app/logs"  # absolute path inside Docker container
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "cache_history.log")

file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=1)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

cache = RedisCache()

# Average arrival delay per airline
avg_delay = cache.compute_aggregation("AIRLINE", "ARRIVAL_DELAY", "mean")

# Fetch only one airline's mean arrival delay from cache
val = cache.get_single_value("mean_ARRIVAL_DELAY_per_AIRLINE", "AA")
print("AA: American Airlines average arrival delay:", val)

# Maximum number of cancelled flights per airport
max_cancelled = cache.compute_aggregation("ORIGIN_AIRPORT", "CANCELLED", "max")

# Fetch only one airline's mean cancellation from cache
val2 = cache.get_single_value("max_CANCELLED_per_ORIGIN_AIRPORT", "EWR")
print("EWR: Newark max cancelation :", val2)

# Standard deviation of arrival delay per airline
std_delay = cache.compute_aggregation("AIRLINE", "ARRIVAL_DELAY", "std")

# Fetch only one airline's stdev arrival delay from cache
val3 = cache.get_single_value("std_ARRIVAL_DELAY_per_AIRLINE", "UA")
print("UA: United Airlines standard deviation of arrival delay:", val3)

# Invalidate just one
cache.invalidate_cache("mean_ARRIVAL_DELAY_per_AIRLINE")

# Clear everything
cache.clear_all_cache()



