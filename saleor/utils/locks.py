from django.core.cache import cache


class RedisBlockingCounterManager:
    """
    Usage:
        with RedisBlockingCounterManager(name='name', ttl=60) as manager:
            # do not put your code here
            if manager.lock:
                pass # blocking staff
                if manager.get() > 0:
                    pass # recall staff
            # and here
    """

    ttl = None
    name = None
    lock = None

    def __init__(self, name: str, ttl: int = 60):
        self.name = name
        self.ttl = ttl

    def __enter__(self):
        self.lock = cache.set(self.name, 0, self.ttl, nx=True)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.lock:
            cache.delete(self.name)
        else:
            cache.set(self.name, (cache.get(self.name) or 0) + 1, self.ttl)

    def get(self) -> int:
        return cache.get(self.name) or 0
