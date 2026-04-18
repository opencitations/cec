#!/usr/bin/env python3
"""Bulk citation extraction + enrichment via the CEC extractor service.

Sends PDFs to the extractor API (which calls GROBID with consolidateHeader +
consolidateCitations enabled by default) and unpacks the returned zip per file.
Detects GROBID's CrossRef rate-limit hits via `docker logs grobid` and retries
indefinitely with exponential backoff until the PDF succeeds.

Stdlib only. Assumes the docker-compose stack in this repo is running
(grobid + extractor on localhost:5001).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


BASE_URL = "http://localhost:5001"
API_PATH = "/cex/api/extractor"
PDF_MIME = "application/pdf"
TIMEOUT = 1800
GROBID_CONTAINER = "grobid"
RETRY_INITIAL = 10.0
RETRY_FACTOR = 3.0
RETRY_MAX = 1800.0
RATE_LIMIT_PATTERN = "Consolidation service returns error (429)"


def iter_pdfs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            raise ValueError(f"not a PDF: {input_path}")
        return [input_path.resolve()]
    if not input_path.is_dir():
        raise ValueError(f"input does not exist: {input_path}")
    pdfs: list[Path] = []
    for root, _, files in os.walk(input_path):
        for name in files:
            if name.lower().endswith(".pdf") and not name.startswith("."):
                pdfs.append((Path(root) / name).resolve())
    pdfs.sort()
    return pdfs


def _multipart_body(
    pdf_path: Path, fields: dict[str, str]
) -> tuple[bytes, str]:
    boundary = f"----cecbulk{uuid.uuid4().hex}"
    crlf = b"\r\n"
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(f"--{boundary}".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"'.encode()
        )
        parts.append(b"")
        parts.append(value.encode())
    parts.append(f"--{boundary}".encode())
    parts.append(
        (
            'Content-Disposition: form-data; '
            f'name="input_files_or_archives"; filename="{pdf_path.name}"'
        ).encode()
    )
    mime = mimetypes.guess_type(pdf_path.name)[0] or PDF_MIME
    parts.append(f"Content-Type: {mime}".encode())
    parts.append(b"")
    parts.append(pdf_path.read_bytes())
    parts.append(f"--{boundary}--".encode())
    parts.append(b"")
    body = crlf.join(parts)
    return body, boundary


def _http_post(url: str, pdf_path: Path, fields: dict[str, str]) -> dict:
    body, boundary = _multipart_body(pdf_path, fields)
    req = urlrequest.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))
    with urlrequest.urlopen(req, timeout=TIMEOUT) as resp:
        payload = resp.read()
    return json.loads(payload)


def _http_download(url: str, dest: Path) -> None:
    req = urlrequest.Request(url, method="GET")
    with urlrequest.urlopen(req, timeout=TIMEOUT) as resp, dest.open("wb") as fh:
        shutil.copyfileobj(resp, fh)


def _normalize_download_url(url: str) -> str:
    if "/cex/api/download/" not in url:
        return url
    suffix = url.split("/cex/api/download/", 1)[1]
    return f"{BASE_URL.rstrip('/')}/cex/api/download/{suffix}"


def _flatten_timestamp_dir(out_dir: Path, stem: str) -> None:
    for child in out_dir.iterdir():
        if child.is_dir() and child.name.startswith(f"{stem}_"):
            for item in child.iterdir():
                target = out_dir / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(target))
            child.rmdir()


def _grobid_saw_rate_limit(since: datetime) -> bool:
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    proc = subprocess.run(
        ["docker", "logs", GROBID_CONTAINER, "--since", since_str],
        capture_output=True, text=True, timeout=30, check=False,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    return RATE_LIMIT_PATTERN in blob


def _do_extraction(pdf: Path, out_dir: Path) -> None:
    fields = {
        "perform_alignment": "false",
        "create_rdf": "false",
        "max_workers": "1",
    }
    api_url = f"{BASE_URL.rstrip('/')}{API_PATH}"
    payload = _http_post(api_url, pdf, fields)

    download_url = payload.get("download_url")
    if not download_url:
        raise RuntimeError(f"no download_url in response: {payload}")
    download_url = _normalize_download_url(download_url)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _http_download(download_url, tmp_path)
        with zipfile.ZipFile(tmp_path) as zf:
            zf.extractall(out_dir)
    finally:
        tmp_path.unlink(missing_ok=True)

    _flatten_timestamp_dir(out_dir, pdf.stem)

    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        entries = manifest if isinstance(manifest, list) else [manifest]
        for entry in entries:
            if isinstance(entry, dict) and entry.get("status") == "error":
                raise RuntimeError(f"extractor error: {entry.get('error')}")


def process_one(pdf: Path, output_root: Path) -> None:
    out_dir = output_root / pdf.stem
    attempt = 0
    while True:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        t0 = datetime.now(timezone.utc) - timedelta(seconds=2)
        try:
            _do_extraction(pdf, out_dir)
            extract_ok = True
        except (HTTPError, URLError, zipfile.BadZipFile, TimeoutError,
                RuntimeError, json.JSONDecodeError) as exc:
            print(f"  extraction error on {pdf.name}: {exc}")
            extract_ok = False

        if extract_ok and not _grobid_saw_rate_limit(t0):
            return

        sleep_for = min(RETRY_INITIAL * (RETRY_FACTOR ** attempt), RETRY_MAX)
        reason = "rate limit" if extract_ok else "extraction failure"
        print(f"  {reason} on {pdf.name}: retry #{attempt + 1} in {sleep_for:.0f}s")
        time.sleep(sleep_for)
        attempt += 1


def run(pdfs: list[Path], output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    total = len(pdfs)
    print(f"processing {total} PDF(s)")

    for i, pdf in enumerate(pdfs, start=1):
        process_one(pdf, output_root)
        elapsed = time.monotonic() - started
        print(f"[{i}/{total}] ok  {pdf.name}  ({elapsed:.1f}s)")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="PDF file or directory of PDFs")
    p.add_argument(
        "-o", "--output", type=Path, default=Path("cec_output"),
        help="output directory (default: ./cec_output)",
    )
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        pdfs = iter_pdfs(args.input)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not pdfs:
        print("no PDFs found", file=sys.stderr)
        return 1
    run(pdfs, args.output.resolve())
    print(f"done: {len(pdfs)} ok")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
