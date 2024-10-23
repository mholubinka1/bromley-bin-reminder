from requests_html import HTMLSession


def download_webpage(url: str) -> bytes:
    session = HTMLSession()
    response = session.get(
        url=url,
    )
    response.html.render()
    return response.content
