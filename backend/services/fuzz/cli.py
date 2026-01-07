#!/usr/bin/env python3
import argparse
import json
from .generators import generate_cases
from .runner import run_case
from .archiver import archive
from .report import to_markdown
from .metrics_exporter import start_exporter
import sys

def main():
    ap = argparse.ArgumentParser(description='Simple API Fuzz CLI')
    ap.add_argument('--endpoint', required=True, help='Target URL (http://...)')
    ap.add_argument('--method', default='GET')
    ap.add_argument('--params', default='{}', help='Base params as JSON')
    ap.add_argument('--tag', default='default', help='Archive tag')
    ap.add_argument('--metrics-port', type=int, default=9108, help='Prometheus exporter port')
    ap.add_argument('--output', default=None, help='Write markdown report to file path')
    args = ap.parse_args()
    # start metrics exporter
    start_exporter(args.metrics_port)

    base_params = json.loads(args.params)
    cases = generate_cases(args.endpoint, args.method, base_params)
    results = []
    for p in cases:
        r = run_case(args.endpoint, args.method, p)
        rd = r.__dict__
        results.append(rd)
        if not r.ok:
            archive(rd, tag=args.tag)
    md = to_markdown(results)
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(md)
        except Exception as e:
            print('Failed to write output:', e, file=sys.stderr)
        else:
            print('Report written to', args.output)
    else:
        print(md)

if __name__ == '__main__':
    main()
