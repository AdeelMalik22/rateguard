
class MemoryStorage:

    def __init__(self):
        self.data = {}


    def get(self, key):
        return self.data.get(key)


    def set(self, key, value):
        self.data[key] = value


    def delete(self, key):
        if key in self.data:
            del self.data[key]