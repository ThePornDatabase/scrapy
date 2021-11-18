import json

from requests.models import Response
from .http import Http


class FlareSolverr:
    __session = None

    def __init__(self, base_url: str):
        self.__BASE_URL = base_url
        self.__API_URL = f'{self.__BASE_URL}/v1'
        self.__session = self.__set_session()

    def __del__(self):
        if self.__session:
            Http.post(self.__API_URL, json={'cmd': 'sessions.destroy', 'session': self.__session})

    def __set_session(self) -> str:
        sessions = self.__get_sessions()
        if sessions:
            session = sessions[0]
        else:
            session = self.__create_session()

        return session

    def __create_session(self) -> str:
        req = Http.post(self.__API_URL, json={'cmd': 'sessions.create'})

        session = None
        if req and req.ok:
            session = req.json()['session']

        return session

    def __get_sessions(self) -> list:
        req = Http.post(self.__API_URL, json={'cmd': 'sessions.list'})
        sessions = None
        if req and req.ok:
            sessions = req.json()['sessions']

        return sessions

    def __request(self, url: str, method: str, **kwargs) -> Response | None:
        cookies = kwargs.pop('cookies', {})
        data = kwargs.pop('data', {})
        method = method.lower()

        if not self.__session:
            return

        if method not in ['get', 'post']:
            return

        params = {
            'cmd': f'request.{method}',
            'session': self.__session,
            'url': url,
        }

        if method == 'post':
            params['postData'] = data

        if cookies:
            if isinstance(cookies, dict):
                cookies = [{'name': name, 'value': value} for name, value in cookies.items()]
            params['cookies'] = json.dumps(cookies)

        req = Http.post(self.__API_URL, json=params)
        if req and req.ok:
            resp = req.json()['solution']
            headers = resp['headers']
            cookies = {cookie['name']: cookie['value'] for cookie in resp['cookies']}

            return Http.fake_response(url, int(resp['headers']['status']), resp['response'], headers, cookies)

        return

    def get(self, url: str, **kwargs):
        return self.__request(url, 'GET', **kwargs)

    def post(self, url: str, **kwargs):
        return self.__request(url, 'POST', **kwargs)
