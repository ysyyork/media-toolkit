"""Loopback-only media preview server with HTTP byte-range support."""
from __future__ import annotations

import argparse
import functools
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class ReviewHandler(SimpleHTTPRequestHandler):
    """Allow native browser video controls to seek without downloading copies."""

    remaining: int | None = None

    def send_head(self):
        self.remaining = None
        header = self.headers.get("Range")
        if not header:
            return super().send_head()
        path = Path(self.translate_path(self.path))
        if not path.is_file():
            return super().send_head()
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
        size = path.stat().st_size
        if not match or not size or not any(match.groups()):
            self.send_error(416, "Unsupported byte range")
            return None
        first, last = match.groups()
        start = int(first) if first else max(0, size - int(last))
        end = min(int(last), size - 1) if first and last else size - 1
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        stream = path.open("rb")
        stream.seek(start)
        self.remaining = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self.remaining))
        self.end_headers()
        return stream

    def end_headers(self):
        if self.remaining is None:
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def copyfile(self, source, outputfile):
        remaining = self.remaining
        try:
            while remaining is None or remaining > 0:
                block = source.read(128 * 1024 if remaining is None else min(128 * 1024, remaining))
                if not block:
                    break
                outputfile.write(block)
                if remaining is not None:
                    remaining -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            # Seeking cancels the previous request; this is normal browser use.
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Folder containing local review media")
    parser.add_argument("--port", type=int, default=8769)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    if not root.is_dir():
        parser.error("directory must be a folder")
    handler = functools.partial(ReviewHandler, directory=str(root))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Local preview: http://127.0.0.1:{args.port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
