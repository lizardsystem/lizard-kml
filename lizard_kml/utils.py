from django.core.cache import cache
from django.conf import settings

from hashlib import sha1
from functools import wraps

def cache_result(seconds=900, ignore_cache=False):
    """
    Cache the result of a function call for the specified number of seconds, 
    using Django's caching mechanism.
    Assumes that the function never returns None (as the cache returns None to indicate a miss),
    and that the function's result only depends on its parameters.
    Note that the ordering of parameters is important. e.g. myFunction(x=1, y=2), myFunction(y=2, x=1),
    and myFunction(1, 2) will each be cached separately.

    Usage:

    @cache(600)
    def my_expensive_method(parm1, parm2, parm3):
        ....
        return expensive_result
    """
    def do_cache_result(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
                key = sha1(str(f.__module__) + str(f.__name__) + str(args) + str(kwargs)).hexdigest()
                result = cache.get(key)
                if ignore_cache or settings.DEBUG or result is None:
                    result = f(*args, **kwargs)
                    cache.set(key, result, seconds)
                return result
        return wrapper
    return do_cache_result
