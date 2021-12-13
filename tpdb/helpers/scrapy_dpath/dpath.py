import dpath.util


class ScrapyDPath:
    __result = None

    def __init__(self, obj, selector, separator='/'):
        _dpath = None
        try:
            _dpath = dpath.util.values(obj, selector, separator=separator)
        except:
            pass

        if _dpath:
            self.__result = [str(res) for res in _dpath]

    def __repr__(self):
        return repr(self.__result)

    def __len__(self):
        return len(self.__result) if self.__result else 0

    def __iter__(self):
        yield self.__result

    def get(self):
        return self.__result[0] if self.__result else None

    def getall(self):
        return self.__result if self.__result else None
