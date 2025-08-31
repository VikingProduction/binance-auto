import os
import logging
import yaml
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type
import requests

def setup_logger(name='trading_bot'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('bot.log')
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def load_config(path='config.yml'):
    with open(path) as f:
        return yaml.safe_load(f)

def validate_env():
    required = ['API_KEY','API_SECRET']
    for key in required:
        if not os.getenv(key):
            raise EnvironmentError(f"Missing required secret: {key}")

@retry(
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    wait=wait_exponential_jitter(initial=1, max=32),
    stop=stop_after_attempt(5)
)
def safe_api_call(func, *args, **kwargs):
    """Effectue func(*args, **kwargs) avec retry exponentiel + jitter."""
    return func(*args, **kwargs)
