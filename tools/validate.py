#!/usr/bin/env python3
"""Validate registry entries without fetching or executing publisher content."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SAFE = re.compile(r"[A-Za-z0-9_.-]+\Z")
MAX_FILE = 4 * 1024 * 1024


def object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    data = path.read_bytes()
    if not data or len(data) > MAX_FILE:
        raise ValueError(f"invalid file size: {path}")
    return data, json.loads(data, object_pairs_hook=object_no_duplicates)


def safe_relative(value):
    return isinstance(value, str) and bool(value) and all(
        part not in (".", "..") and SAFE.fullmatch(part)
        for part in value.split("/")
    )


def validate_entry(root, manifest_path):
    root = root.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    if not manifest_path.is_relative_to(root / "entries") or manifest_path.name != "manifest.json":
        raise ValueError("manifest is outside the entries tree")
    _, m = read_json(manifest_path)
    if set(m) != {"schema_version", "id", "profile", "environment", "reference", "provenance", "coverage"}:
        raise ValueError("unsupported manifest fields")
    if m["schema_version"] != 1 or not SAFE.fullmatch(m["id"]):
        raise ValueError("unsupported manifest version or id")
    if m["id"] != manifest_path.parent.name or m["profile"] != "azure-snp-vtpm-ima/1":
        raise ValueError("entry path/profile mismatch")
    environment = m["environment"]
    if set(environment) != {"tee", "product", "os", "kernel_release", "kernel_package"}:
        raise ValueError("invalid environment metadata")
    if environment["tee"] != "AMD SEV-SNP" or environment["product"] not in ("Milan", "Genoa"):
        raise ValueError("unsupported platform")
    if not all(isinstance(v, str) and 0 < len(v) <= 200 for v in environment.values()):
        raise ValueError("invalid environment value")
    reference = m["reference"]
    if set(reference) != {"path", "sha256", "ima_entries"}:
        raise ValueError("invalid reference metadata")
    if not safe_relative(reference["path"]):
        raise ValueError("unsafe reference path")
    reference_path = root / reference["path"]
    if reference_path.resolve(strict=True) != manifest_path.parent / "reference.json":
        raise ValueError("reference must be adjacent to manifest")
    if not isinstance(reference["sha256"], str) or not HEX64.fullmatch(reference["sha256"]):
        raise ValueError("invalid reference digest")
    data, trs = read_json(reference_path)
    if hashlib.sha256(data).hexdigest() != reference["sha256"]:
        raise ValueError("reference digest mismatch")
    if not isinstance(trs, dict) or not isinstance(trs.get("ima_measurements"), list):
        raise ValueError("invalid IMA reference")
    entries = trs["ima_measurements"]
    if not entries or len(entries) != reference["ima_entries"] or type(reference["ima_entries"]) is not int:
        raise ValueError("IMA entry count mismatch")
    if not isinstance(trs.get("pcr10_sha256"), str) or not HEX64.fullmatch(trs["pcr10_sha256"]):
        raise ValueError("missing SHA-256 PCR 10")
    if not all(isinstance(e, dict) and e.get("PCR") == 10 for e in entries):
        raise ValueError("invalid IMA entry")
    provenance = m["provenance"]
    if set(provenance) != {"kind", "collected_on", "review_status", "description"}:
        raise ValueError("invalid provenance metadata")
    if provenance["kind"] not in ("observed-stage-evidence", "reproduced-build"):
        raise ValueError("unknown provenance kind")
    if provenance["review_status"] not in ("stage-candidate", "stage-approved", "approved"):
        raise ValueError("unknown review status")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", provenance["collected_on"]):
        raise ValueError("invalid collection date")
    if not isinstance(provenance["description"], str) or len(provenance["description"]) > 1000:
        raise ValueError("invalid provenance description")
    if m["coverage"] != ["boot_aggregate", "kernel_modules"]:
        raise ValueError("unsupported coverage claim")
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = p.parse_args()
    root = args.root.resolve(strict=True)
    files = sorted((root / "entries").glob("**/manifest.json"))
    if not files:
        raise SystemExit("no manifests")
    for path in files:
        m = validate_entry(root, path)
        print(f"PASS {m['id']} {m['reference']['sha256']}")


if __name__ == "__main__":
    main()
