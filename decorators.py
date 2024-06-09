import time


def timed_cache(seconds):
    def decorator(func):
        cache = {}
        
        async def wrapped(*args, **kwargs):
            # key = (args, tuple(kwargs.items()))
            key = args[0].__class__.__name__
            current_time = time.time()
            
            # Check if cache is valid
            if key in cache:
                value, timestamp = cache[key]
                if current_time - timestamp < seconds:
                    return value
            
            # Call the function and store the result in cache
            result = await func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
        
        return wrapped
    return decorator