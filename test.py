from tpdb.helpers.http import Http


def main():
    url = 'https://www.dorcelclub.com/en/scene/200107/erotic-evening'
    url = Http.get(url)
    print(url)


if __name__ == '__main__':
    main()
