#!/usr/bin/python
import os
import glob
import pandas
import numpy as np
import tasks
import pylab


def recurse_directory(location):
    result_file_pattern = os.path.join(location, 'results_CTOOLS_HOURLY_*_Output.csv')
    results_file_names = glob.glob(result_file_pattern)
    for file_name in results_file_names:
        process_results(file_name)
    else:
        all_files_pattern = os.path.join(location, '*')
        all_files = glob.glob(all_files_pattern)
        directories = filter(os.path.isdir, all_files)
        for directory in directories:
            recurse_directory(directory)


def process_results(file_name):
    df = pandas.read_csv(file_name)
    distance_col, concentration_col = df.columns[0], df.columns[-1]
    distances, concentrations = np.array(df[distance_col]), np.array(df[concentration_col])
    if not all(concentrations):
        return False
    bezier_curve, opts = tasks.fit_model_output(distances, concentrations)
    Y = bezier_curve(distances, *opts)
    fig, ax = pylab.subplots()
    ax.plot(distances, Y)
    ax.plot(distances, concentrations)
    fig.show()
    print "foo!"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("location")
    args = parser.parse_args()
    if args.location:
        recurse_directory(args.location)


if __name__ == "__main__":
    main()
