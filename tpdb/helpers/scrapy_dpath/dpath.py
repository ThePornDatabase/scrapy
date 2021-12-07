import dpath.util


class ScrapyDPath:
    def __init__(self, obj, selector, separator='/'):
        self.__result = None

        _dpath = None
        try:
            _dpath = dpath.util.values(obj, selector, separator=separator)
        except:
            pass

        if _dpath:
            self.__result = _dpath

    def __repr__(self):
        return repr(self.__result)

    def __len__(self):
        if self.__result:
            return len(self.__result)

        return 0

    def __iter__(self):
        yield self.__result

    def get(self):
        if self.__result:
            return self.__result[0]

        return None

    def getall(self):
        print(self.__result)
        if self.__result:
            return self.__result

        return None
