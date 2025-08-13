import logging
from datetime import datetime, timedelta

def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        return None

def get_date_range(start_date, end_date):
    start = parse_date(start_date)
    end = parse_date(end_date)
    if start and end:
        return [start + timedelta(days=x) for x in range((end-start).days + 1)]
    return []

def truncate_text(text, max_length=100):
    return text[:max_length] + '...' if len(text) > max_length else text

# Add other utility functions as needed