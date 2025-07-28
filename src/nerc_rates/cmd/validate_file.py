#!/usr/bin/env python3

import argparse
import sys

import pydantic
import yaml

from nerc_rates import outages, rates


def pydantic_to_github(err, filename, file_type):
    """Produce a github error annotation from a pydantic ValidationError"""
    for error in err.errors():
        if file_type == "outages":
            print(f"::error file={filename},title=Outages validation error::{error['msg']}")
        else:
            print(f"::error file={filename},title=Rates validation error::{error['msg']}")


def yaml_to_github(err, filename, file_type):
    """Produce a github error annotation from a YAML ParserError"""
    if hasattr(err, 'problem_mark') and err.problem_mark:
        line = err.problem_mark.line
        print(
            f"::error file={filename},line={line},title={file_type.capitalize()} parser error::{err.context}: {err.problem}"
        )
    else:
        print(f"::error file={filename},title={file_type.capitalize()} parser error::{err}")


def main():
    p = argparse.ArgumentParser(description="Validate NERC outages or rates files")
    p.add_argument(
        "-g", "--github", action="store_true", help="Emit github workflow annotations"
    )
    p.add_argument("-u", "--url", action="store_true", help="File is a url")
    p.add_argument(
        "-t", "--type",
        choices=["outages", "rates"],
        required=True,
        help="Type of file to validate"
    )
    p.add_argument("file", help="Path to the file to validate")
    args = p.parse_args()

    try:
        if args.type == "outages":
            if args.url:
                data = outages.load_from_url(args.file)
            else:
                data = outages.load_from_file(args.file)
            print(f"OUTAGES VALIDATION OK [{len(data.root)} entries]")
        else:  # rates
            if args.url:
                data = rates.load_from_url(args.file)
            else:
                data = rates.load_from_file(args.file)
            print(f"RATES VALIDATION OK [{len(data.root)} entries]")

    except pydantic.ValidationError as err:
        if args.github:
            pydantic_to_github(err, args.file, args.type)
        else:
            print(f"{args.type.capitalize()} validation error: {err}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as err:
        if args.github:
            yaml_to_github(err, args.file, args.type)
        else:
            print(f"{args.type.capitalize()} YAML parsing error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
