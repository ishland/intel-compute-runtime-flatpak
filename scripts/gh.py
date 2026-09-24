import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
RETRIES = 4
FLATHUB_SDK = "org.freedesktop.Sdk"

# Release tags of intel/compute-runtime look like 26.35.39758.10; the legacy
# line is 24.35.30872.36. intel-graphics-compiler tags look like v2.41.5.
LEGACY_PREFIX = "24.35."


def token():
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def get(path, accept="application/vnd.github+json"):
    url = path if path.startswith("http") else API + path
    for attempt in range(1, RETRIES + 1):
        request = urllib.request.Request(url, headers={"Accept": accept})
        token_ = token()
        if token_:
            request.add_header("Authorization", "Bearer " + token_)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code < 500:
                raise
            failure = error
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError) as error:
            failure = error
        if attempt == RETRIES:
            raise failure
        print("retrying %s (%s)" % (url, failure), file=sys.stderr)
        time.sleep(2 ** attempt)


def asset_json(repo, tag, name):
    try:
        release = get("/repos/%s/releases/tags/%s" % (repo, tag))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    for asset in release.get("assets", []):
        if asset["name"] == name:
            return get("/repos/%s/releases/assets/%d" % (repo, asset["id"]),
                       accept="application/octet-stream")
    return None


def newest_sdks(count):
    branches = get("https://flathub.org/api/v2/summary/%s" % FLATHUB_SDK)["branches"]
    versions = [branch for branch in branches if tag_key(branch)]
    return sorted(versions, key=tag_key, reverse=True)[:count]


def delete(path):
    request = urllib.request.Request(API + path, method="DELETE",
                                     headers={"Accept": "application/vnd.github+json"})
    token_ = token()
    if token_:
        request.add_header("Authorization", "Bearer " + token_)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404
        raise


def get_all(path, max_pages=10):
    items = []
    for page in range(1, max_pages + 1):
        separator = "&" if "?" in path else "?"
        batch = get("%s%sper_page=100&page=%d" % (path, separator, page))
        items.extend(batch)
        if len(batch) < 100:
            break
    return items


def emit(values):
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a") as handle:
            for key, value in values.items():
                handle.write("%s=%s\n" % (key, value))
    else:
        print(json.dumps(values))


def tag_key(tag):
    parts = tag.lstrip("v").split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def series_of(tag, legacy_prefix=LEGACY_PREFIX):
    if tag_key(tag) is None:
        return None
    return "legacy" if tag.startswith(legacy_prefix) else "main"


def newest_version(releases, series, legacy_prefix=LEGACY_PREFIX):
    tags = [release["tag_name"] for release in releases
            if series_of(release["tag_name"], legacy_prefix) == series]
    return max(tags, key=tag_key) if tags else None
