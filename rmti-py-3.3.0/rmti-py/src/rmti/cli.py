"""Command line.   rmti selfcheck | version | keys new | serve"""
import argparse
import json
import sys

from . import __version__
from .domains import hcc, urban


def _report(title, rows, ok):
    print(f"\n{title}")
    for name, field, exp, got, good in rows:
        print(f"  {name:<32} {field:<8} paper={exp:<6} code={got:<6} {'OK' if good else 'MISMATCH'}")
    print(f"  -> {'all match' if ok else 'MISMATCHES FOUND'}")


def _keys_new(a) -> int:
    from .api.security import client_entry, generate_key
    key = generate_key()
    entry = client_entry(a.name, a.org or a.name, [s for s in a.scopes.split(",") if s], a.rate, key)
    print("API key (shown ONCE; give it to the client, do not store it):\n  " + key)
    print("\nAdd this entry to the RMTI_API_CLIENTS JSON list on the server (it holds only the hash):")
    print(json.dumps(entry, indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rmti", description="Risk Mechanism Theory Index")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selfcheck", help="reproduce the published tables")
    sub.add_parser("version")
    k = sub.add_parser("keys", help="API key management").add_subparsers(dest="kcmd", required=True).add_parser("new", help="mint a key")
    k.add_argument("--name", required=True)
    k.add_argument("--org", default="")
    k.add_argument("--scopes", default="score,batch,fhir", help="comma list from: score,batch,fhir")
    k.add_argument("--rate", type=int, default=60, help="requests per minute")
    s = sub.add_parser("serve", help="run the API (needs rmti-py[api])")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    a = ap.parse_args(argv)
    if a.cmd == "version":
        print(__version__)
        return 0
    if a.cmd == "keys":
        return _keys_new(a)
    if a.cmd == "serve":
        import uvicorn
        uvicorn.run("rmti.api:app", host=a.host, port=a.port)
        return 0
    rows, ok1 = urban.selfcheck()
    _report("Urban (IJMADA 2026, Tables 4-5)", rows, ok1)
    rows, ok2 = hcc.selfcheck()
    _report("HCC (preprint, Tables 1-2)", rows, ok2)
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
