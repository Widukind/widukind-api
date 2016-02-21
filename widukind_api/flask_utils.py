import hashlib
from flask import request

def func_cache_with_args(func_name, **kwargs):
    """Return hash value from func name and request.full_path
    """
    return hashlib.sha256(func_name.encode("utf-8") + request.full_path.encode("utf-8")).hexdigest()

