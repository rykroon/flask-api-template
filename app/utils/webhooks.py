from dataclasses import dataclass
import httpx
import json


@dataclass
class Webhook:
    url: str
    data: dict
    secret_key: str = None

    def send_via_http(self):
        with httpx.Client() as client:
            req = self._create_request()
            resp = client.send(req)
        return resp.is_success

    def _create_request(self):
        content = json.dumps(self.data)
        request = httpx.Request(
            method='POST',
            url=self.url,
            content=content
        )
        request.headers['Content-Type'] = 'application/json'
        return request
