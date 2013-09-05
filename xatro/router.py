class Router(object):


    def __init__(self, mapping=None, instance=None):
        self._mapping = mapping or {}
        self._instance = instance


    def __get__(self, instance, type=None):
        return Router(self._mapping, instance)


    def call(self, key, *args, **kwargs):
        func = self._mapping[key]
        return func(self._instance, *args, **kwargs)


    def handle(self, key):
        def deco(f):
            self._mapping[key] = f
            return f
        return deco