#!/usr/bin/python
import os
import glob
import tasks


def recurse_directory(location, local=False):
    input_file = os.path.join(location, "CTOOLS_Inputs.txt")
    if os.path.isfile(input_file):
        run_models(location, local)
    else:
        all_files_pattern = os.path.join(location, '*')
        all_files = glob.glob(all_files_pattern)
        directories = filter(os.path.isdir, all_files)
        for directory in directories:
            recurse_directory(directory, local)


def run_models(location, local=False):
    if os.path.isfile(os.path.join(location, "roads.csv")):
        if local:
            tasks.run_model("ROAD", location)
        else:
            tasks.run_model.delay("ROAD", location)
    elif os.path.isfile(os.path.join(location, "railways.csv")):
        if local:
            tasks.run_model("RAIL", location)
        else:
            tasks.run_model.delay("RAIL", location)
    elif os.path.isfile(os.path.join(location, "points.csv")):
        if local:
            tasks.run_model("POINT", location)
        else:
            tasks.run_model.delay("POINT", location)
    elif os.path.isfile(os.path.join(location, "area.csv")):
        if local:
            tasks.run_model("AREA", location)
        else:
            tasks.run_model.delay("AREA", location)
    elif os.path.isfile(os.path.join(location, "sit.csv")):
        if local:
            tasks.run_model("SIT", location)
        else:
            tasks.run_model.delay("SIT", location)
    else:
        raise ValueError("No source file located")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("location")
    parser.add_argument("--local", action="store_true", default=False)
    args = parser.parse_args()
    if args.location:
        recurse_directory(args.location, args.local)


if __name__ == "__main__":
    main()