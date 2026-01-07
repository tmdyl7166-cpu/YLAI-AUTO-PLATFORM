#!/usr/bin/env python3
import argparse
from .sources.abuseipdb import AbuseIPDBCollector
from .sources.shodan_api import ShodanAPICollector
from .report import to_markdown
from ..common.env import load_env, get

def main():
    ap = argparse.ArgumentParser(description='Collectors Aggregate CLI')
    ap.add_argument('--ip', required=False)
    ap.add_argument('--hostname', required=False)
    ap.add_argument('--output', default='frontend/reports/collectors_report.md')
    args = ap.parse_args()

    load_env()
    items = []

    # AbuseIPDB by IP
    abuse_key = get('ABUSEIPDB_KEY')
    if abuse_key and args.ip:
        c1 = AbuseIPDBCollector(api_key=abuse_key)
        items.append(c1.collect({'ip': args.ip}))

    # Shodan by IP or hostname
    shodan_key = get('SHODAN_KEY')
    if shodan_key and (args.ip or args.hostname):
        c2 = ShodanAPICollector(api_key=shodan_key)
        q = {'ip': args.ip} if args.ip else {'hostname': args.hostname}
        items.append(c2.collect(q))

    if not items:
        raise SystemExit('No collectors ran (missing keys or inputs). Set ABUSEIPDB_KEY/SHODAN_KEY in .env and pass --ip/--hostname')

    md = to_markdown(items)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(md)
    print('Collectors report written to', args.output)

if __name__ == '__main__':
    main()
