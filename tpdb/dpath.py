import dpath.util

class _dpath(): 
    def __init__(self, selector, separator='/'):
        self.result = []

        try:
            self.dpath = dpath.util.search(self, selector, separator=separator, yielded=True)
        except:
            pass

        if self.dpath:
            for x in self.dpath: 
                self.result.append(x[1])

    def __repr__(self):
        return repr(self.result)

    def __len__(self):
        return len(self.result)

    def __iter__(self):
        yield self.result

    def get(self):
        if self.result:
            return self.result[0]

        return ''

    def getall(self):
        return self.result
