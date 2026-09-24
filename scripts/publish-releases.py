#!/usr/bin/env python3
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

UPSTREAM = "https://github.com/intel/compute-runtime/releases/tag/%s"

NOTES = """\
Intel OpenCL driver bundles for the freedesktop runtime branches {sdks}:

- `org.freedesktop.Platform.GL.OpenCLIntel` for Gen12 and newer
- `org.freedesktop.Platform.GL.OpenCLIntelLegacy` for Gen8, Gen9 and Gen11

| series | upstream | intel-graphics-compiler | libigdgmm12 |
|---|---|---|---|
{series}

{checksums}

See README.md for more information.

"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", default="bundles",
                        help="directory holding the downloaded artifact directories")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--tag", help="release tag (default: the current UTC time)")
    parser.add_argument("--main", default="", help="current compute-runtime version")
    parser.add_argument("--legacy", default="", help="legacy compute-runtime version")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def checksum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def collect(artifacts):
    entries = []
    for entry in sorted(os.listdir(artifacts)):
        directory = os.path.join(artifacts, entry)
        report = os.path.join(directory, "release.json")
        if not os.path.exists(report):
            print("skipping %s: no release.json" % directory, file=sys.stderr)
            continue
        with open(report) as handle:
            info = json.load(handle)
        assets = sorted(glob.glob(os.path.join(directory, "*.flatpak")))
        assets += sorted(glob.glob(os.path.join(directory, "*.yaml")))
        if not assets:
            print("skipping %s: no bundles" % directory, file=sys.stderr)
            continue
        entries.append((info, assets))
    return entries


def notes_for(versions, rows):
    series = "\n".join("| %s | [%s](%s) | %s | %s |"
                       % (name, info["version"], UPSTREAM % info["version"],
                          info["igc"], info["gmmlib"])
                       for name, info in sorted(versions["series"].items()))
    table = ["| bundle | sha256 |", "|---|---|"]
    table += ["| `%s` | `%s` |" % (os.path.basename(path), checksum(path))
              for path in rows]
    return NOTES.format(sdks=", ".join(versions["sdks"]), series=series,
                        checksums="\n".join(table) + "\n\n")


def main():
    args = parse_args()
    if not args.repo:
        sys.exit("--repo (or $GITHUB_REPOSITORY) is required")

    entries = collect(args.artifacts)
    if not entries:
        sys.exit("no bundles found in %s" % args.artifacts)

    per_series = {}
    for info, _ in entries:
        per_series.setdefault(info["series"], info)
    main = args.main or per_series.get("main", {}).get("version", "")
    legacy = args.legacy or per_series.get("legacy", {}).get("version", "")
    tag = args.tag or datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")

    versions = {"main": main, "legacy": legacy, "series": per_series,
                "sdks": sorted({info["sdk"] for info, _ in entries}, reverse=True),
                "igc": {name: info["igc"] for name, info in per_series.items()},
                "gmmlib": {name: info["gmmlib"] for name, info in per_series.items()}}
    assets = [path for _, group in entries for path in group]
    rows = [path for path in assets if path.endswith(".flatpak")]
    notes = notes_for(versions, rows)

    with open(os.path.join(args.artifacts, "versions.json"), "w") as handle:
        json.dump({key: value for key, value in versions.items() if key != "series"},
                  handle, indent=2, sort_keys=True)
        handle.write("\n")
    assets.append(os.path.join(args.artifacts, "versions.json"))

    title = "%s + legacy %s" % (main, legacy) if legacy else main
    print("releasing %s: %s" % (tag, [os.path.basename(path) for path in assets]))
    if args.dry_run:
        print(notes)
        return

    command = ["gh", "release", "create", tag, "--repo", args.repo,
               "--title", title, "--notes-file", "-"]
    if os.environ.get("GITHUB_SHA"):
        command += ["--target", os.environ["GITHUB_SHA"]]
    subprocess.run(command + assets, check=True, input=notes.encode())


if __name__ == "__main__":
    main()
