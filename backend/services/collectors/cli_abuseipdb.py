#!/usr/bin/env python3
import argparse
from .sources.abuseipdb import AbuseIPDBCollector
from .report import to_markdown
from ..common.env import load_env, get

def main():
    ap = argparse.ArgumentParser(description='AbuseIPDB Collect CLI')
    ap.add_argument('--ip', required=True)
    ap.add_argument('--output', default='frontend/reports/collectors_report.md')
    args = ap.parse_args()

    load_env()
    key = get('ABUSEIPDB_KEY')
    if not key:
        raise SystemExit('ABUSEIPDB_KEY not set in env/.env')
    c = AbuseIPDBCollector(api_key=key)
    item = c.collect({'ip': args.ip})
    md = to_markdown([item])
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(md)
    print('Collectors report written to', args.output)

if __name__ == '__main__':
    main()
