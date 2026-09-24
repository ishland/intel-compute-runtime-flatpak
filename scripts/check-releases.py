#!/usr/bin/env python3
import argparse
import json
import os
import sys

from gh import asset_json, emit, get_all, newest_release, newest_sdks, newest_version

UPSTREAM_REPO = "intel/compute-runtime"

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", default=UPSTREAM_REPO, help="upstream repository to watch")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""),
                        help="repository the bundles are published to")
    parser.add_argument("--series", default="both", choices=("both", "main", "legacy"),
                        help="restrict the check to a single series")
    parser.add_argument("--version", help="package this exact upstream version instead of the newest")
    parser.add_argument("--sdks", help="freedesktop SDK branches to build for "
                                       "(default: the newest --sdk-count ones)")
    parser.add_argument("--sdk-count", type=int, default=3,
                        help="how many of the newest SDK branches to build for")
    parser.add_argument("--legacy-prefix", default="24.35.",
                        help="tag prefix that identifies the legacy line")
    parser.add_argument("--force", action="store_true",
                        help="build even when the version already has a release")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.repo:
        sys.exit("--repo (or $GITHUB_REPOSITORY) is required")

    if args.version and args.series == "both":
        sys.exit("--version needs --series main or --series legacy")

    upstream = get_all("/repos/%s/releases" % args.upstream)
    main = args.version or newest_version(upstream, "main", args.legacy_prefix)
    legacy = newest_version(upstream, "legacy", args.legacy_prefix)
    if not main:
        sys.exit("no upstream release found")
    sdks = args.sdks.split() if args.sdks else newest_sdks(args.sdk_count)

    # Releases are tagged with the time they were built and always carry both
    # drivers, so one changed series rebuilds the pair. What the newest release
    # already contains is in its versions.json.
    published = asset_json(args.repo, newest_release(args.repo), "versions.json") or {}
    changed = args.force or any(published.get(series) != version
                                for series, version in (("main", main), ("legacy", legacy)))

    wanted = []
    for series, version in (("main", main), ("legacy", legacy)):
        if args.series not in ("both", series):
            continue
        if not version:
            print("no %s release found upstream" % series, file=sys.stderr)
            continue
        if not changed:
            print("%s %s is already released, skipping" % (series, version), file=sys.stderr)
            continue
        for sdk in sdks:
            wanted.append({"series": series, "version": version, "sdk": sdk})

    matrix = {"include": wanted}
    print("build matrix: %s" % json.dumps(matrix), file=sys.stderr)
    emit({"matrix": json.dumps(matrix), "has_work": "true" if wanted else "false",
          "main": main, "legacy": legacy or "", "sdks": " ".join(sdks)})


if __name__ == "__main__":
    main()
