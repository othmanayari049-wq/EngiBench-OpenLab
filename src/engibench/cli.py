from __future__ import annotations

import argparse
import json

from .parser import parse_line
from .serial_io import available_ports


def main() -> None:
    parser = argparse.ArgumentParser(prog="engibench", description="EngiBench OpenLab utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ports", help="List available serial ports")
    parse_cmd = sub.add_parser("parse", help="Parse one telemetry line")
    parse_cmd.add_argument("line")
    args = parser.parse_args()

    if args.command == "ports":
        for port in available_ports():
            print(port)
    elif args.command == "parse":
        sample = parse_line(args.line, source="cli")
        print(json.dumps({"timestamp": sample.timestamp, "source": sample.source, **sample.values}, indent=2))


if __name__ == "__main__":
    main()
