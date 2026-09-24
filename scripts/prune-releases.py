#!/usr/bin/env python3
import argparse
import os
import sys

from gh import delete, get_all


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--keep", type=int, default=5, help="releases to keep per series")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.repo:
        sys.exit("--repo (or $GITHUB_REPOSITORY) is required")

    releases = [release for release in get_all("/repos/%s/releases" % args.repo)
                if not release["draft"]]
    releases.sort(key=lambda release: release["created_at"], reverse=True)

    for release in releases[args.keep:]:
        tag = release["tag_name"]
        print("deleting release %s (keeping %s)"
              % (tag, [r["tag_name"] for r in releases[:args.keep]]))
        if args.dry_run:
            continue
        delete("/repos/%s/releases/%d" % (args.repo, release["id"]))
        delete("/repos/%s/git/refs/tags/%s" % (args.repo, tag))


if __name__ == "__main__":
    main()
