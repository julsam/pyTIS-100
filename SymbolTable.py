
class SymbolTable(object):
    def __init__(self):
        self.table = {}

    def get(self, key):
        if self.has(key):
            return self.table[key]
        return None

    def get_key(self, value):
        for k, v in self.table.iteritems():
            if v == value:
                return k
        return None

    def add(self, key, value):
        if self.has(key):
            Exception("The identifier %s is already present in the symbol table" % key)
        self.table[key] = int(value)

    def has(self, key):
        return key in self.table

    def __repr__(self):
        return "%s" % self.table