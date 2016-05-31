import os
import glob
import tasks

def recurse_directory(location):
    input_file = os.path.join(location, "CTOOLS_Inputs.txt")
    if os.path.isfile(input_file):
        run_models(location)
    else:
        all_files_pattern = os.path.join(location, '*')
        all_files = glob.glob(all_files_pattern)
        directories = filter(os.path.isdir, all_files)
        for directory in directories:
            recurse_directory(directory)


def run_models(location):
    has_roads = os.path.isfile(location, "roads.csv")
    has_railways = os.path.isfile(location, "railways.csv")
    has_ships_in_transit = os.path.isfile(location, "sit.csv")
    has_points = os.path.isfile(location, "points.csv")
    has_areas = os.path.isfile(location, "areas.csv")
    if has_roads and has_railways and has_ships_in_transit and has_points and has_areas:
        tasks.run_model.delay(location, "all")
    else:
        if has_roads:
            tasks.run_model.delay(location, "road")
        if has_railways:
            tasks.run_model.delay(location, "railway")
        if has_points:
            tasks.run_model.delay(location, "points")
        if has_areas:
            tasks.run_model.delay(location, "areas")
        if has_ships_in_transit:
            tasks.run_model.delay(location, "sit")
