import requests

USER_AGENT = "Secrover"

RequestException = requests.RequestException


def request(method: str, url: str, **kwargs) -> requests.Response:
    headers = {"User-Agent": USER_AGENT, **kwargs.pop("headers", {})}
    return requests.request(method, url, headers=headers, **kwargs)


def get(url: str, **kwargs) -> requests.Response:
    return request("GET", url, **kwargs)
