import os


class Configuration(dict):
    def __init__(self):
        super().__init__(os.environ)

    def __getitem__(self, key):
        key_lower = key.lower()
        for k, v in self.items():
            if k.lower() == key_lower:
                return v
        return None
