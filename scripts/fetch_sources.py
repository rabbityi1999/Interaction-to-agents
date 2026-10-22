"""Fetch small, pinned upstream examples. Does not execute upstream projects."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import urllib.request


def verify(data, record):
    if len(data) != record['bytes']:
        raise ValueError(f"Size mismatch: {record['file']}")
    if hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError(f"SHA256 mismatch: {record['file']}")
    blob = b'blob ' + str(len(data)).encode() + b'\0' + data
    if hashlib.sha1(blob).hexdigest() != record['git_blob_sha']:
        raise ValueError(f"Git blob hash mismatch: {record['file']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    args = parser.parse_args()
    root = args.data_dir.resolve()
    lock = Path(__file__).resolve().parents[1] / 'config/sources.lock.json'
    records = json.loads(lock.read_text(encoding='utf-8'))
    for record in records:
        path = (root / record['file']).resolve()
        path.relative_to(root)
        if path.exists():
            verify(path.read_bytes(), record)
            print('Verified cached:', record['file'], flush=True)
            continue
        request = urllib.request.Request(
            record['url'], headers={'User-Agent': 'Interaction-to-agents-audit'}
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read(8_000_001)
        if len(payload) > 8_000_000:
            raise ValueError('Unexpectedly large response')
        blob = json.loads(payload)
        if blob.get('encoding') != 'base64':
            raise ValueError('Expected GitHub blob API base64 response')
        data = base64.b64decode(blob['content'])
        verify(data, record)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        print('Downloaded and verified:', record['file'], flush=True)
    print(f'Verified {len(records)} files; no full-corpus download.')


if __name__ == '__main__':
    main()
