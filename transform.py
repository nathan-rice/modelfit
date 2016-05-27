import pandas
import math
import pyproj
import os
import load
import json
import numpy as np

_lambert = pyproj.Proj("+proj=lcc +lat_1=33 +lat_2=45 +lat_0=40 +lon_0=-97 +x_0=0 +y_0=0 +ellps=GRS80 "
                       "+datum=NAD83 +units=m +no_defs")


def latlong_dist(p0, p1):
    (p0_lon, p0_lat) = _lambert(p0[0], p0[1], inverse=True)
    (p1_lon, p1_lat) = _lambert(p1[0], p1[1], inverse=True)
    return math.sqrt((p1_lon - p0_lon) ** 2 + (p1_lat - p0_lat) ** 2)


def generate_receptors_df_for_line(startx, starty, endx, endy, num_receptors=50, receptor_offset=10):
    delta_x = endx - endy
    delta_y = endy - starty
    slope = delta_x / delta_y
    perpendicular_slope = - 1 / slope
    midpoint_x = startx + delta_x / 2
    midpoint_y = starty + delta_y / 2
    midpoint = (midpoint_x, midpoint_y)
    theta = math.atan(perpendicular_slope)
    dx = math.cos(theta) * receptor_offset
    dy = math.sin(theta) * receptor_offset
    x_receptors = [midpoint_x + i * dx for i in range(num_receptors)]
    y_receptors = [midpoint_y + i * dy for i in range(num_receptors)]
    distance = [str(latlong_dist(p, midpoint)) for p in zip(x_receptors, y_receptors)]
    raw_data = {"id": distance, "x": x_receptors, "y": y_receptors}
    return pandas.DataFrame(raw_data, columns=["id", "x", "y"])


def generate_receptors_for_point(x, y, num_receptors=50, receptor_offset=10):
    x_receptors = [x + i * receptor_offset for i in range(num_receptors)]
    y_receptors = [y] * num_receptors
    p0 = (x, y)
    distance = [str(latlong_dist(p, p0)) for p in zip(x_receptors, y_receptors)]
    raw_data = {"id": distance, "x": x_receptors, "y": y_receptors}
    return pandas.DataFrame(raw_data, columns=["id", "x", "y"])


def road_to_dataframe(road):
    df = pandas.DataFrame(columns=["id", "from_x", "from_y", "to_x", "to_y", "sf_id", "stfips", "ctfips", "fclass_rev",
                                   "aadt", "mph", "gas_car_multiplier", "gas_truck_multiplier", "diesel_car_multiplier",
                                   "diesel_truck_multiplier"])
    road_dict = {col: getattr(road, col, 1) for col in df.columns}
    return df.append([road_dict])


def generate_receptors_df_for_road(road, num_receptors=50, receptor_offset=10):
    return generate_receptors_df_for_line(road.from_x, road.from_y, road.to_x, road.to_y, num_receptors,
                                          receptor_offset)


def input_file_parameter_combinations():
    met_conditions = range(1, 3)
    seasons = range(1, 3)
    days = range(1, 3)
    hours = range(1, 5)
    pollutants = range(1, 14)
    for met_condition in met_conditions:
        for season in seasons:
            for day in days:
                for hour in hours:
                    for pollutant in pollutants:
                        yield {"met_condition": met_condition, "season": season, "day": day, "hour": hour,
                               "pollutant": pollutant}


def mkdir(dir_name):
    try:
        os.mkdir(dir_name)
    except OSError as err:
        if not err.errno == 17:
            raise


def generate_run_files(location, source_df, input_parameters):
    parameters = {c: getattr(source_df, c)[0] for c in source_df.columns}
    parameters.update(input_parameters)
    generate_parameter_file(location, parameters)
    generate_input_file(location, input_parameters)


def generate_parameter_file(location, input_parameters):
    parameter_file = os.path.join(location, "parameters.json")
    parameter_data = json.dumps(input_parameters)
    with open(parameter_file, 'w') as f:
        f.write(parameter_data)


def generate_input_file(location, input_parameters):
    input_file = os.path.join(location, "CTOOLS_Inputs.txt")
    with open('templates/CTOOLS_Inputs.txt') as f:
        template = f.read()
    input_contents = template.format(**input_parameters)
    with open(input_file, 'w') as f:
        f.write(input_contents)


def generate_road_run_configurations(road, location):
    road_sub_dir = os.path.join(location, str(road.id))
    mkdir(road_sub_dir)
    receptor_df = generate_receptors_df_for_road(road)
    road_df = road_to_dataframe(road)
    for (i, combination) in enumerate(input_file_parameter_combinations()):
        run_dir = os.path.join(road_sub_dir, str(i))
        mkdir(run_dir)
        receptor_df.to_csv(os.path.join(run_dir, "receptors.csv"), index=False)
        road_df.to_csv(os.path.join(run_dir, "roads.csv"), index=False)
        generate_run_files(run_dir, road_df, combination)


def generate_road_sets(location):
    road_dir = os.path.join(location, "roads")
    mkdir(location)
    mkdir(road_dir)
    roads = load.load_example_roads()
    for road in roads:
        print "generating configurations for road ", str(road.id)
        generate_road_run_configurations(road, road_dir)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("location")
    parser.add_argument("--road", action="store_true")
    args = parser.parse_args()
    if args.road:
        generate_road_sets(args.location)


if __name__ == "__main__":
    main()

