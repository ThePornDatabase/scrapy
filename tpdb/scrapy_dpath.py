import dpath.util

class scrapy_dpath(): 
    def __init__(self, response, selector):
        self.result = []

        try:
            self.dpath = dpath.util.search(response, selector, yielded=True)
        except:
            pass

        if self.dpath:
            for x in self.dpath: 
                self.result.append(x[1])

    def get(self):
        if self.result:
            return self.result[0]

        return ''

    def getall(self):
        return self.result
