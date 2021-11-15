import json

from .http import Http


class FlareSolverr:
    _session = None

    def __init__(self, base_url: str):
        self._BASE_URL = base_url
        self._API_URL = f'{self._BASE_URL}/v1'

        self._session = self._set_session()

    def __del__(self):
        if self._session:
            Http.post(self._API_URL, json={'cmd': 'sessions.destroy', 'session': self._session})

    def _set_session(self):
        sessions = self._get_sessions()
        if sessions:
            session = sessions[0]
        else:
            session = self._create_session()

        return session

    def _create_session(self):
        req = Http.post(self._API_URL, json={'cmd': 'sessions.create'})

        session = None
        if req and req.ok:
            session = req.json()['session']

        return session

    def _get_sessions(self):
        req = Http.post(self._API_URL, json={'cmd': 'sessions.list'})
        sessions = None
        if req and req.ok:
            sessions = req.json()['sessions']

        return sessions

    def _request(self, url, method, **kwargs):
        cookies = kwargs.pop('cookies', {})
        post_data = kwargs.pop('data', {})

        method = method.lower()

        if not self._session:
            return

        if method not in ['get', 'post']:
            return

        data = {
            'cmd': f'request.{method}',
            'session': self._session,
            'url': url,
        }

        if method == 'post':
            data['postData'] = json.dumps(post_data)

        if cookies:
            if isinstance(cookies, dict):
                cookies = [{'name': name, 'value': value} for name, value in cookies.items()]
            data['cookies'] = json.dumps(cookies)

        req = Http.post(self._API_URL, json=data)

        if req and req.ok:
            data = req.json()['solution']
            headers = data['headers']
            cookies = {cookie['name']: cookie['value'] for cookie in data['cookies']}

            return Http.fake_response(req, url, int(data['headers']['status']), data['response'], headers, cookies)

        return None

    def get(self, url, **kwargs):
        return self._request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._request(url, 'POST', **kwargs)
