"""TEST ONLY: synthetic Box transport. No credentials and no external network."""
import base64
from email.parser import BytesParser
from email.policy import default
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import urllib.error
import urllib.parse
import urllib.request


def deny_network(*a, **kw):
    raise AssertionError("external network is forbidden in tests")


socket.socket.connect = deny_network
socket.create_connection = deny_network


def add_surrogate_to_request(req, credential, entry_name, allowed_hosts):
    assert urllib.parse.urlparse(req.full_url).hostname in allowed_hosts
    req.add_header("Authorization", "Bearer hsurr:synthetic")


def read_response_body(response):
    return response.read()


class Response(io.BytesIO):
    def __init__(self, data, status=200, content_type="application/json"):
        super().__init__(data)
        self.status = status
        self.headers = {"Content-Type": content_type}


class SyntheticOpener:
    def open(self, req, timeout=None):
        path = Path(os.environ["BOX_TEST_STATE"])
        state = json.loads(path.read_text())
        parsed = urllib.parse.urlparse(req.full_url)
        query = urllib.parse.parse_qs(parsed.query)
        route = parsed.path
        def meta(item):
            data = base64.b64decode(item["data"])
            return {"id": item["id"], "type": "file", "name": item["name"],
                    "size": len(data), "sha1": hashlib.sha1(data).hexdigest(),
                    "file_version": {"id": item["version"]}, "parent": {"id": item["parent"]}}
        if route == "/2.0/users/me":
            value = {"id": "100", "type": "user", "name": "Synthetic QA", "login": "qa@example.invalid"}
        elif route.endswith("/files/content") and req.get_method() == "POST":
            if state.get("deny_upload"):
                raise urllib.error.HTTPError(req.full_url, 403, "denied", {}, io.BytesIO(b'{"code":"access_denied"}'))
            message = BytesParser(policy=default).parsebytes(
                ("Content-Type: " + req.get_header("Content-type") + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + req.data)
            parts = list(message.iter_parts())
            attributes = json.loads(parts[0].get_payload(decode=True))
            data = parts[1].get_payload(decode=True)
            item = {"id": str(1000 + len(state["files"])), "name": attributes["name"],
                    "parent": attributes["parent"]["id"], "version": "1", "data": base64.b64encode(data).decode()}
            state["files"].append(item); state["posts"] = state.get("posts", 0) + 1
            path.write_text(json.dumps(state))
            return Response(json.dumps({"entries": [meta(item)]}).encode(), 201)
        elif route == "/2.0/search" or ("/folders/" in route and route.endswith("/items")):
            folder = query.get("ancestor_folder_ids", [None])[0] if route.endswith("search") else route.split("/")[-2]
            items = [meta(f) for f in state["files"] if folder is None or f["parent"] == folder]
            if route.endswith("search"):
                term = query.get("query", [""])[0].lower()
                items = [f for f in items if term in f["name"].lower()]
            offset = int(query.get("offset", [0])[0]); limit = int(query.get("limit", [100])[0])
            value = {"entries": items[offset:offset+limit], "offset": offset, "limit": limit, "total_count": len(items)}
        elif route.startswith("/2.0/files/"):
            file_id = route.split("/")[3]
            item = next((f for f in state["files"] if f["id"] == file_id), None)
            if item is None:
                raise urllib.error.HTTPError(req.full_url, 404, "missing", {}, io.BytesIO(b"{}"))
            if route.endswith("/content"):
                return Response(base64.b64decode(item["data"]), content_type="text/plain")
            value = meta(item)
        else:
            raise AssertionError("unexpected synthetic request " + route)
        return Response(json.dumps(value).encode())


# Explicitly injected by the test runner's PYTHONPATH, never shipped to Muse.
urllib.request.build_opener = lambda *a, **kw: SyntheticOpener()
