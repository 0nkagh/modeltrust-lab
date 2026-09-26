"""
Research prototype. No audit functionality in this version.

Exit code convention:
0: Success
1: Unexpected internal error
2: Usage error (argparse default)
3: Not implemented yet
4: Input/validation error (schema fail, file not found, etc.)
"""

import argparse
import sys
import json
import traceback
from datetime import datetime, timezone
from typing import Optional

from modeltrust.dataio import read_table
from modeltrust.schema import ColumnSpec
from modeltrust.provenance import build_provenance
from modeltrust.errors import ModelTrustError, InputError

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="modeltrust", description="Diagnostic audits for ML evaluation trustworthiness.")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--traceback", action="store_true", help="Show full traceback on internal errors")
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # Existing commands (not implemented)
    commands = ["report"]
    for cmd in commands:
        sub_parser = subparsers.add_parser(cmd)
        sub_parser.add_argument("-i", "--input", required=True, help="Input data file (CSV/Parquet)")
        sub_parser.add_argument("--group-col", help="Column name for group-based splits/errors")
        sub_parser.add_argument("--time-col", help="Column name for temporal leakage/splits")
        sub_parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
        sub_parser.add_argument("--out-dir", help="Output directory for reports")

    def _add_common_args(p):
        p.add_argument("-i", "--input", required=True, help="Input data file (CSV/Parquet)")
        p.add_argument("--target-col", help="Target column")
        p.add_argument("--pred-col", help="Prediction column")
        p.add_argument("--group-col", help="Group column")
        p.add_argument("--time-col", help="Time column")
        p.add_argument("--subset-col", help="Subset column")
        p.add_argument("--format", choices=["csv", "parquet"], help="File format")
        p.add_argument("--delimiter", help="CSV delimiter")
        p.add_argument("--encoding", default="utf-8-sig", help="File encoding (default utf-8-sig)")
        p.add_argument("--decimal", choices=["dot", "comma"], help="Decimal separator")
        p.add_argument("--max-rows", type=int, help="Max rows to read")
        p.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
        p.add_argument("--run-timestamp", action="store_true", help="Add wall-clock timestamp to provenance")
        p.add_argument("--out-dir", help="Output directory for reports (reserved)")

    # New command: inspect
    inspect_parser = subparsers.add_parser("inspect")
    _add_common_args(inspect_parser)

    # Profile command
    profile_parser = subparsers.add_parser("profile")
    _add_common_args(profile_parser)

    # Leakage command
    leakage_parser = subparsers.add_parser("leakage")
    _add_common_args(leakage_parser)
    
    # Split command
    split_parser = subparsers.add_parser("split")
    _add_common_args(split_parser)
    split_parser.add_argument("--mode", choices=["random", "group", "temporal", "all"], default="all")
    split_parser.add_argument("--test-size", type=float, default=0.2)

    args = parser.parse_args(argv)

    if args.version:
        from modeltrust import __version__
        print(f"modeltrust {__version__}")
        return 0

    if args.command in commands:
        print("not implemented yet (planned: PHASE 2 / T4+)", file=sys.stderr)
        return 3

    if args.command in ["inspect", "profile", "leakage", "split"]:
        if args.out_dir:
            print("--out-dir is reserved; no files are written in this version", file=sys.stderr)

        if args.command == "split":
            if args.mode in ["group", "temporal"]:
                if args.mode == "group" and not args.group_col:
                    print("Error: --mode group requires --group-col", file=sys.stderr)
                    return 4
                if args.mode == "temporal" and not args.time_col:
                    print("Error: --mode temporal requires --time-col", file=sys.stderr)
                    return 4

        try:
            loaded = read_table(
                args.input,
                fmt=args.format,
                delimiter=args.delimiter,
                encoding=args.encoding,
                decimal=args.decimal,
                max_rows=args.max_rows
            )
            
            # set decimal for provenance if provided
            if args.decimal:
                loaded.meta["decimal"] = args.decimal
            else:
                loaded.meta["decimal"] = "dot"
                
            spec = ColumnSpec(
                target=args.target_col,
                prediction=args.pred_col,
                group=args.group_col,
                time=args.time_col,
                subset=args.subset_col
            )
            
            prov = build_provenance(loaded, spec, seed=args.seed, path_as_given=args.input)
            
            if args.run_timestamp:
                prov["run_metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
                
            if args.command == "profile":
                from modeltrust.profile import build_profile
                prov["profile"] = build_profile(loaded.frame, loaded.meta, spec)
                
            if args.command == "leakage":
                from modeltrust.audit.leakage import build_leakage
                prov["leakage"] = build_leakage(loaded.frame, spec)
                
            if args.command == "split":
                from modeltrust.audit.split import build_split
                prov["split"] = build_split(loaded.frame, spec, args.mode, args.test_size, args.seed)

                
            if prov["schema"]["summary"]["fail"] > 0:
                for check in prov["schema"]["checks"]:
                    if check["result"] == "fail":
                        print(check["detail"], file=sys.stderr)
                return 4
                
            # print json
            print(json.dumps(prov, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
            
            return 0
            
        except InputError as e:
            print(str(e), file=sys.stderr)
            return 4
        except Exception as e:
            print(f"Internal error: {e}", file=sys.stderr)
            if args.traceback:
                traceback.print_exc(file=sys.stderr)
            return 1

    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
