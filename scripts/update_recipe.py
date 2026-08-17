#!/usr/bin/env python3
"""Bump a julia-forge recipe.yaml to the version juliaup's channel currently points to.

Resolves a juliaup channel (e.g. "release", "lts") to a concrete Julia version
using juliaup's own hosted versiondb, then looks up the per-platform download
URL and sha256 for that version from the same upstream versions.json that
juliaup's own scripts/versiondb/updateversiondb.jl consumes. Only rewrites the
`version:` and `url:`/`sha256:` scalars in place, so recipe.yaml formatting
stays stable across runs.
"""

import argparse
import json
import os
import re
import sys
import urllib.request

DEFAULT_SERVER = "https://julialang-s3.julialang.org"

# Maps each recipe `if:` selector to the platform triplet used in upstream
# versions.json / juliaup's versiondb.
PLATFORM_TRIPLETS = {
    "osx and arm64": "aarch64-apple-darwin14",
    "osx and x86_64": "x86_64-apple-darwin14",
    "linux and aarch64": "aarch64-linux-gnu",
    "linux and ppc64le": "powerpc64le-linux-gnu",
    "linux and x86_64": "x86_64-linux-gnu",
    "win and x86_64": "x86_64-w64-mingw32",
}

# Reference platform used only to resolve channel -> version. Version numbers
# are platform-independent, and every channel is guaranteed present here.
REFERENCE_TARGET = "x86_64-unknown-linux-gnu"

# Tier 3 platforms: upstream doesn't reliably publish a build for every
# point release, so a missing archive here is not fatal -- the selector's
# existing source block is left untouched instead of aborting the run.
OPTIONAL_SELECTORS = {"linux and ppc64le"}


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def fetch_json(url):
    return json.loads(fetch(url))


def resolve_channel_version(server, channel):
    dbversion = fetch(f"{server}/juliaup/DBVERSION").decode().strip()
    versiondb = fetch_json(
        f"{server}/juliaup/versiondb/versiondb-{dbversion}-{REFERENCE_TARGET}.json"
    )
    channels = versiondb["AvailableChannels"]
    if channel not in channels:
        raise SystemExit(
            f"juliaup channel '{channel}' not found in versiondb "
            f"(dbversion {dbversion}). Available: {sorted(channels)}"
        )
    full_version = channels[channel]["Version"]
    return full_version.split("+", 1)[0]


def find_platform_file(versions_data, version, triplet):
    entry = versions_data.get(version)
    if entry is None:
        return None
    for file in entry["files"]:
        if (
            file["triplet"] == triplet
            and file["kind"] == "archive"
            and file["extension"] == "tar.gz"
        ):
            return file
    return None


def current_version(text):
    match = re.search(r"^context:\s*\n\s*version:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def update_source_block(text, selector, url, sha256):
    pattern = re.compile(
        r"(- if:\s*" + re.escape(selector) + r"\s*\n\s*then:\s*\n\s*- url:\s*)"
        r"([^\n]+)"
        r"(\n\s*sha256:\s*)"
        r"([^\n]+)"
    )
    new_text, count = pattern.subn(
        lambda m: m.group(1) + url + m.group(3) + sha256, text, count=1
    )
    if count != 1:
        raise SystemExit(f"Could not find a source block for selector '{selector}' to update.")
    return new_text


def update_version(text, version):
    pattern = re.compile(r"(context:\s*\n\s*version:\s*)(\S+)")
    new_text, count = pattern.subn(lambda m: m.group(1) + version, text, count=1)
    if count != 1:
        raise SystemExit("Could not find context.version to update.")
    return new_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe", help="Path to a julia-forge recipe.yaml")
    parser.add_argument(
        "--channel", required=True, help="juliaup channel to track, e.g. release or lts"
    )
    args = parser.parse_args()

    server = os.environ.get("JULIAUP_SERVER", DEFAULT_SERVER)

    version = resolve_channel_version(server, args.channel)

    with open(args.recipe, encoding="utf-8") as f:
        text = f.read()

    if current_version(text) == version:
        print(f"{args.recipe}: already up to date at {version} ({args.channel})")
        return

    versions_data = fetch_json(f"{server}/bin/versions.json")

    resolved = {}
    for selector, triplet in PLATFORM_TRIPLETS.items():
        if f"- if: {selector}\n" not in text:
            continue
        file = find_platform_file(versions_data, version, triplet)
        if file is None:
            if selector in OPTIONAL_SELECTORS:
                print(
                    f"{args.recipe}: no '{triplet}' tar.gz archive found for Julia "
                    f"{version} (selector '{selector}'); leaving this Tier 3 "
                    f"platform's source block unchanged.",
                    file=sys.stderr,
                )
                continue
            raise SystemExit(
                f"{args.recipe}: no '{triplet}' tar.gz archive found for Julia "
                f"{version} (selector '{selector}'). Refusing to update any "
                f"platform until this is resolved by hand (e.g. remove that "
                f"platform's source block if upstream dropped it)."
            )
        resolved[selector] = file

    new_text = update_version(text, version)
    for selector, file in resolved.items():
        new_text = update_source_block(new_text, selector, file["url"], file["sha256"])

    with open(args.recipe, "w", encoding="utf-8") as f:
        f.write(new_text)

    print(f"{args.recipe}: updated to {version} ({args.channel})")


if __name__ == "__main__":
    main()
