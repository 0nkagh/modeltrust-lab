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
    
    commands = []
    
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("-i", "--input", required=True, help="Input data file (CSV/Parquet)")
    report_parser.add_argument("--target-col", help="Target column")
    report_parser.add_argument("--pred-col", help="Prediction column")
    report_parser.add_argument("--group-col", help="Group column")
    report_parser.add_argument("--time-col", help="Time column")
    report_parser.add_argument("--subset-col", help="Subset column")
    report_parser.add_argument("--format", choices=["csv", "parquet"], help="File format")
    report_parser.add_argument("--delimiter", help="CSV delimiter")
    report_parser.add_argument("--encoding", default="utf-8-sig", help="File encoding (default utf-8-sig)")
    report_parser.add_argument("--decimal", choices=["dot", "comma"], help="Decimal separator")
    report_parser.add_argument("--max-rows", type=int, help="Max rows to read")
    report_parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    report_parser.add_argument("--run-timestamp", action="store_true", help="Add wall-clock timestamp to provenance")
    report_parser.add_argument("--out-dir", help="Output directory for reports")
    report_parser.add_argument("--mode", choices=["random", "group", "temporal", "all"], default="all")
    report_parser.add_argument("--test-size", type=float, default=0.2)
    report_parser.add_argument("--evaluate", action="store_true", help="Include model evaluation in report")
    report_parser.add_argument("--model", choices=["mean", "ols", "both"], default="both")
    report_parser.add_argument("--split-mode", choices=["random", "group", "temporal"], default="random")
    report_parser.add_argument("--cv", choices=["none", "random", "group", "temporal"], default="none")
    report_parser.add_argument("--folds", type=int, default=5)
    report_parser.add_argument("--shift", action="store_true", help="Include distribution shift and OOD checks in report")
    report_parser.add_argument("--lower-col", help="Lower bound column for uncertainty intervals")
    report_parser.add_argument("--upper-col", help="Upper bound column for uncertainty intervals")
    report_parser.add_argument("--nominal-coverage", type=float, help="Nominal coverage level (e.g. 0.9 for 90%)")

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

    # New command: card
    card_parser = subparsers.add_parser("card")
    _add_common_args(card_parser)
    card_parser.add_argument("--mode", choices=["random", "group", "temporal", "all"], default="all")
    card_parser.add_argument("--test-size", type=float, default=0.2)
    card_parser.add_argument("--model", choices=["mean", "ols", "both"], default="both")
    card_parser.add_argument("--split-mode", choices=["random", "group", "temporal"], default="random")
    card_parser.add_argument("--cv", choices=["none", "random", "group", "temporal"], default="none")
    card_parser.add_argument("--folds", type=int, default=5)
    card_parser.add_argument("--lower-col", help="Lower bound column for uncertainty intervals")
    card_parser.add_argument("--upper-col", help="Upper bound column for uncertainty intervals")
    card_parser.add_argument("--nominal-coverage", type=float, help="Nominal coverage level (e.g. 0.9 for 90%)")

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

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate")
    _add_common_args(eval_parser)
    eval_parser.add_argument("--model", choices=["mean", "ols", "both"], default="both")
    eval_parser.add_argument("--split-mode", choices=["random", "group", "temporal"], default="random")
    eval_parser.add_argument("--test-size", type=float, default=0.2)
    eval_parser.add_argument("--cv", choices=["none", "random", "group", "temporal"], default="none")
    eval_parser.add_argument("--folds", type=int, default=5)
    eval_parser.add_argument("--lower-col", help="Lower bound column for uncertainty intervals")
    eval_parser.add_argument("--upper-col", help="Upper bound column for uncertainty intervals")
    eval_parser.add_argument("--nominal-coverage", type=float, help="Nominal coverage level (e.g. 0.9 for 90%)")

    # Shift command
    shift_parser = subparsers.add_parser("shift")
    _add_common_args(shift_parser)
    shift_parser.add_argument("--split-mode", choices=["random", "group", "temporal"], default="random")
    shift_parser.add_argument("--test-size", type=float, default=0.2)

    args = parser.parse_args(argv)
    
    actual_argv = argv if argv is not None else sys.argv

    if args.version:
        from modeltrust import __version__
        print(f"modeltrust {__version__}")
        return 0

    if args.command in commands:
        print("not implemented yet (planned: PHASE 2 / T4+)", file=sys.stderr)
        return 3

    if args.command in ["inspect", "profile", "leakage", "split", "evaluate", "shift"]:
        if args.out_dir:
            print('use "modeltrust report --out-dir" to write report files', file=sys.stderr)
            return 0

    if args.command in ["report", "card"]:
        if not args.out_dir:
            print(f"Error: --out-dir is required for {args.command} command", file=sys.stderr)
            return 2

        # Flags exclusive to --evaluate
        evaluate_only_flags = ["--pred-col", "--model", "--cv", "--folds", "--lower-col", "--upper-col", "--nominal-coverage"]
        # Flags valid with --evaluate OR --shift
        evaluate_or_shift_flags = ["--split-mode", "--test-size"]

        cmd = getattr(args, "command", "")
        run_eval = getattr(args, "evaluate", False) or (cmd == "card" and getattr(args, "target_col", None))
        run_shift = getattr(args, "shift", False) or (cmd == "card" and getattr(args, "target_col", None))

        if cmd != "card" and not run_eval:
            for flag in evaluate_only_flags:
                if any(a == flag or a.startswith(f"{flag}=") for a in actual_argv):
                    print(f"Error: {flag} requires --evaluate", file=sys.stderr)
                    return 2

        if not run_eval and not run_shift:
            for flag in evaluate_or_shift_flags:
                if any(a == flag or a.startswith(f"{flag}=") for a in actual_argv):
                    print(f"Error: {flag} requires --evaluate or --shift", file=sys.stderr)
                    return 2

        if run_eval:
            if not args.target_col:
                print("Error: --target-col is required when --evaluate is enabled", file=sys.stderr)
                return 2
            if getattr(args, "pred_col", None) and any(a == "--model" or a.startswith("--model=") for a in actual_argv):
                print("Error: --pred-col and --model cannot be used together", file=sys.stderr)
                return 2
            if getattr(args, "split_mode", None) == "group" and not args.group_col:
                print("Error: --split-mode group requires --group-col", file=sys.stderr)
                return 4
            if getattr(args, "split_mode", None) == "temporal" and not getattr(args, "time_col", None):
                print("Error: --split-mode temporal requires --time-col", file=sys.stderr)
                return 4
            if getattr(args, "cv", None) == "group" and not args.group_col:
                print("Error: --cv group requires --group-col", file=sys.stderr)
                return 4
            if getattr(args, "cv", None) == "temporal" and not getattr(args, "time_col", None):
                print("Error: --cv temporal requires --time-col", file=sys.stderr)
                return 4
            if bool(getattr(args, "lower_col", None)) != bool(getattr(args, "upper_col", None)):
                print("Error: --lower-col and --upper-col must be provided together", file=sys.stderr)
                return 2
            if getattr(args, "nominal_coverage", None) is not None and not (0.0 < args.nominal_coverage < 1.0):
                print("Error: --nominal-coverage must be between 0.0 and 1.0 exclusive", file=sys.stderr)
                return 2

        if run_shift:
            if not args.target_col:
                print("Error: --target-col is required when --shift is enabled", file=sys.stderr)
                return 2
            if getattr(args, "split_mode", None) == "group" and not args.group_col:
                print("Error: --split-mode group requires --group-col", file=sys.stderr)
                return 4
            if getattr(args, "split_mode", None) == "temporal" and not getattr(args, "time_col", None):
                print("Error: --split-mode temporal requires --time-col", file=sys.stderr)
                return 4

    if args.command == "evaluate":
        if not args.target_col:
            print("Error: --target-col is required for evaluate command", file=sys.stderr)
            return 2
        if args.pred_col and any(a == "--model" or a.startswith("--model=") for a in actual_argv):
            print("Error: --pred-col and --model cannot be used together", file=sys.stderr)
            return 2
        if args.split_mode == "group" and not args.group_col:
            print("Error: --split-mode group requires --group-col", file=sys.stderr)
            return 4
        if args.split_mode == "temporal" and not args.time_col:
            print("Error: --split-mode temporal requires --time-col", file=sys.stderr)
            return 4
        if args.cv == "group" and not args.group_col:
            print("Error: --cv group requires --group-col", file=sys.stderr)
            return 4
        if args.cv == "temporal" and not args.time_col:
            print("Error: --cv temporal requires --time-col", file=sys.stderr)
            return 4
        if bool(args.lower_col) != bool(args.upper_col):
            print("Error: --lower-col and --upper-col must be provided together", file=sys.stderr)
            return 2
        if args.nominal_coverage is not None and not (0.0 < args.nominal_coverage < 1.0):
            print("Error: --nominal-coverage must be between 0.0 and 1.0 exclusive", file=sys.stderr)
            return 2

    if args.command == "shift":
        if not args.target_col:
            print("Error: --target-col is required for shift command", file=sys.stderr)
            return 2
        if args.split_mode == "group" and not args.group_col:
            print("Error: --split-mode group requires --group-col", file=sys.stderr)
            return 4
        if args.split_mode == "temporal" and not args.time_col:
            print("Error: --split-mode temporal requires --time-col", file=sys.stderr)
            return 4

    if args.command in ["inspect", "profile", "leakage", "split", "report", "card", "evaluate", "shift"]:
        if args.command in ["split", "report", "card"]:
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

            # Column existence validation — card command only
            # (Other sub-commands are out of scope for this release; see D-079.)
            if args.command == "card":
                _input_cols = set(loaded.frame.columns)
                _col_flag_map = [
                    ("--target-col",  getattr(args, "target_col",  None)),
                    ("--pred-col",    getattr(args, "pred_col",    None)),
                    ("--group-col",   getattr(args, "group_col",   None)),
                    ("--time-col",    getattr(args, "time_col",    None)),
                    ("--subset-col",  getattr(args, "subset_col",  None)),
                    ("--lower-col",   getattr(args, "lower_col",   None)),
                    ("--upper-col",   getattr(args, "upper_col",   None)),
                ]
                for _flag, _col in _col_flag_map:
                    if _col and _col not in _input_cols:
                        print(
                            f"Error: {_flag} '{_col}' not found in input columns",
                            file=sys.stderr,
                        )
                        return 2

            prov = build_provenance(loaded, spec, seed=args.seed, path_as_given=args.input)
            
            if args.run_timestamp:
                prov["run_metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
                
            if args.command in ["profile", "report", "card"]:
                from modeltrust.profile import build_profile
                prov["profile"] = build_profile(loaded.frame, loaded.meta, spec)
                
            if args.command in ["leakage", "report", "card"]:
                from modeltrust.audit.leakage import build_leakage
                prov["leakage"] = build_leakage(loaded.frame, spec)
                
            if args.command in ["split", "report", "card"]:
                if args.command in ["report", "card"] and not args.group_col and not args.time_col:
                    prov["split"] = None
                    prov["input"]["warnings"].append("split_not_requested")
                else:
                    from modeltrust.audit.split import build_split
                    prov["split"] = build_split(loaded.frame, spec, args.mode, args.test_size, args.seed)

            if args.command == "evaluate" or getattr(args, "evaluate", False) or (args.command == "card" and args.target_col):
                from modeltrust.evaluate import build_evaluation
                prov["evaluation"] = build_evaluation(
                    loaded.frame, 
                    spec, 
                    model=args.model if not args.pred_col else "supplied", 
                    split_mode=args.split_mode, 
                    test_size=args.test_size, 
                    cv=args.cv, 
                    folds=args.folds, 
                    seed=args.seed,
                    lower_col=getattr(args, "lower_col", None),
                    upper_col=getattr(args, "upper_col", None),
                    nominal_coverage=getattr(args, "nominal_coverage", None)
                )

            if args.command == "shift" or getattr(args, "shift", False) or (args.command == "card" and args.target_col):
                from modeltrust.audit.shift import build_shift
                prov["shift"] = build_shift(
                    loaded.frame,
                    spec,
                    split_mode=args.split_mode,
                    test_size=args.test_size,
                    seed=args.seed
                )
                
            if prov["schema"]["summary"]["fail"] > 0:
                for check in prov["schema"]["checks"]:
                    if check["result"] == "fail":
                        print(check["detail"], file=sys.stderr)
                return 4
                
            if args.command == "report":
                from modeltrust.report import write_reports
                json_p, md_p = write_reports(prov, args.out_dir)
                print(f"wrote {json_p} and {md_p}", file=sys.stderr)
                return 0
                
            if args.command == "card":
                from modeltrust.card import write_card
                # Reconstruct reproduce_command
                import shlex
                reproduce_command = "python -m modeltrust " + " ".join(shlex.quote(a) for a in actual_argv[1:])
                json_p, md_p = write_card(prov, args.out_dir, reproduce_command)
                print(f"wrote {json_p} and {md_p}", file=sys.stderr)
                return 0
            
            # print json
            if args.command == "evaluate":
                eval_prov = {
                    "tool": prov["tool"],
                    "run_metadata": prov["run_metadata"],
                    "environment": prov["environment"],
                    "input": prov["input"],
                    "column_spec": prov["column_spec"],
                    "schema": prov["schema"],
                    "evaluation": prov["evaluation"]
                }
                print(json.dumps(eval_prov, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
            elif args.command == "shift":
                shift_prov = {
                    "tool": prov["tool"],
                    "run_metadata": prov["run_metadata"],
                    "environment": prov["environment"],
                    "input": prov["input"],
                    "column_spec": prov["column_spec"],
                    "schema": prov["schema"],
                    "shift": prov["shift"]
                }
                print(json.dumps(shift_prov, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
            else:
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


