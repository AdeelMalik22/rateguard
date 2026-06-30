class KeyResolver:

    def __init__(self, func=None):
        self.func = func


    def resolve(self, *args, **kwargs):

        if self.func:
            return self.func(*args, **kwargs)

        return "anonymous"