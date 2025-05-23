class BiMap:
    def __init__(self):
        self.reverse = {}
        self.get = {}

    def put(self, key, value):
        self.get[key] = value
        self.reverse[value] = key

    def del ByKey(self, key):
        try:
            del (self.reverse[self.get[key]])
            del (self.get[key])
        except KeyError:
            pass

    def del ByVal(self, val):
        try:
            del (self.get[self.reverse[val]])
            del (self.reverse[val])
        except KeyError:
            pass

    def hasKey(self, key):
        has = True
        try:
            self.get[key]
        except KeyError:
            has = False
        return has

    def hasVal(self, val):
        has = True
        try:
            self.reverse[val]
        except KeyError:
            has = False
        return has
