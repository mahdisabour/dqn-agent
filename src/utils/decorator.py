import time


def retry(max_retries, wait_time):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    time.sleep(wait_time)
            else:
              raise Exception(f"Max retries exceed")
        return wrapper
    return decorator