"""Run the three local diagnostic stages; no network or model calls."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--output-dir', type=Path, default=Path('outputs/reproduction'))
    args = parser.parse_args()
    data, out = args.data_dir.resolve(), args.output_dir.resolve()
    if out.exists():
        parser.error('Output directory exists; choose a new directory to preserve old results.')
    scripts = Path(__file__).resolve().parent
    jobs = [
        ('audit_schema.py', ['--output-dir', str(out / 'schema')]),
        ('audit_visibility.py', ['--output-dir', str(out / 'visibility')]),
        ('check_inputs.py', ['--schema-dir', str(out / 'schema'),
                             '--visibility-dir', str(out / 'visibility')]),
    ]
    for name, extra in jobs:
        command = [sys.executable, '-B', str(scripts / name), '--data-dir', str(data)] + extra
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
        print('Completed:', name, flush=True)
    r = json.loads((out / 'visibility/results.json').read_text(encoding='utf-8'))
    print(json.dumps({k: r[k] for k in (
        'samples', 'private_numeric_hp_retained', 'noncontroller_sample_occurrences',
        'boundary_tests', 'boundary_tests_passed', 'model_calls', 'gpu_calls'
    )}, indent=2))
    print('Output:', out)


if __name__ == '__main__':
    main()
