"""
Research prototype. No audit functionality in this version.

Exit code convention:
0: Success
2: Usage error (argparse default)
3: Not implemented yet
4: Input/validation error (T2+)
"""

import argparse
import sys
from typing import Optional

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="modeltrust", description="Diagnostic audits for ML evaluation trustworthiness.")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    commands = ["profile", "leakage", "split", "report"]
    for cmd in commands:
        sub_parser = subparsers.add_parser(cmd)
        sub_parser.add_argument("-i", "--input", required=True, help="Input data file (CSV/Parquet)")
        sub_parser.add_argument("--group-col", help="Column name for group-based splits/errors")
        sub_parser.add_argument("--time-col", help="Column name for temporal leakage/splits")
        sub_parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
        sub_parser.add_argument("--out-dir", help="Output directory for reports")

    args = parser.parse_args(argv)

    if args.version:
        from modeltrust import __version__
        print(f"modeltrust {__version__}")
        return 0

    if args.command in commands:
        print("not implemented yet (planned: PHASE 2 / T2+)", file=sys.stderr)
        return 3

    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
