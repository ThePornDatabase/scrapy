import json

import requests

from .requests_response import fake_response


class FlareSolverr():
    _session = None

    def __init__(self, base_url: str):
        self._BASE_URL = base_url
        self._API_URL = f'{self._BASE_URL}/v1'

        if not self._is_available():
            return

        self._session = self._set_session()

    def _is_available(self):
        req = None
        try:
            req = requests.head(self._BASE_URL)
        except:
            pass

        if req:
            return req.ok

        return False

    def _set_session(self):
        sessions = self._get_sessions()
        if sessions:
            session = sessions[0]
        else:
            session = self._create_session()

        return session

    def __del__(self):
        if self._session:
            requests.post(self._API_URL, json={'cmd': 'sessions.destroy', 'session': self._session})

    def _create_session(self):
        req = requests.post(self._API_URL, json={'cmd': 'sessions.create'})

        return req.json()['session']

    def _get_sessions(self):
        req = requests.post(self._API_URL, json={'cmd': 'sessions.list'})

        return req.json()['sessions']

    def _request(self, url, method, **kwargs):
        cookies = kwargs.pop('cookies', {})
        post_data = kwargs.pop('post_data', {})

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
            data['cookies'] = json.dumps(cookies)

        req = None
        try:
            req = requests.post(self._API_URL, json=data)
        except:
            pass

        if req and req.ok:
            data = req.json()['solution']
            headers = data['headers']
            cookies = {cookie['name']: cookie['value'] for cookie in data['cookies']}

            return fake_response(req, url, int(data['headers']['status']), data['response'], headers, cookies)

        return None

    def get(self, url, **kwargs):
        return self._request(url, 'get', **kwargs)

    def post(self, url, **kwargs):
        return self._request(url, 'post', **kwargs)
