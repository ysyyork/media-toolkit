"""Attribution sidecar for the selected soundtrack."""
from pathlib import Path


def write_credits(
    path: Path,
    track: str,
    creator: str,
    source: str,
    license_name: str,
    license_url: str,
    start: float,
) -> None:
    path.write_text(
        f'Music: “{track}” by {creator}\n'
        f'Source: {source}\n'
        f'License: {license_name}\n'
        f'{license_url}\n'
        f'Music excerpt trimmed from {start:05.2f}s and faded for this video.\n',
        encoding="utf-8",
    )
