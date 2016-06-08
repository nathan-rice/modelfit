import pandas
import math
import pyproj
import os
import json
import subprocess
import numpy as np
from scipy.optimize import curve_fit, newton
from celery import Celery
from common import mkdir


app = Celery('tasks', broker='amqp://guest@localhost//')
model_dir = "/home/nathan/Projects/CTOOLS_12_07_2015/"
model_executable = "/home/nathan/Projects/CTOOLS_12_07_2015/CTOOLS_HOURLY.ifort.x"
template_location = '/home/nathan/PycharmProjects/modelfit/templates/'


_lambert = pyproj.Proj("+proj=lcc +lat_1=33 +lat_2=45 +lat_0=40 +lon_0=-97 +x_0=0 +y_0=0 +ellps=GRS80 "
                       "+datum=NAD83 +units=m +no_defs")

os.chdir(model_dir)


def latlong_dist(p0, p1):
    (p0_lon, p0_lat) = _lambert(p0[0], p0[1], inverse=True)
    (p1_lon, p1_lat) = _lambert(p1[0], p1[1], inverse=True)
    return math.sqrt((p1_lon - p0_lon) ** 2 + (p1_lat - p0_lat) ** 2)


def generate_receptors_df_for_line(startx, starty, endx, endy, num_receptors=50, receptor_offset=10):
    delta_x = endx - startx
    delta_y = endy - starty
    slope = delta_x / delta_y
    perpendicular_slope = - 1 / slope
    midpoint_x = (startx + endx) / 2
    midpoint_y = (starty + endy) / 2
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
    template_file = os.path.join(template_location, "CTOOLS_Inputs.txt")
    with open(template_file) as f:
        template = f.read()
    input_contents = template.format(**input_parameters)
    with open(input_file, 'w') as f:
        f.write(input_contents)


@app.task
def generate_road_run_configurations(road, location):
    road_sub_dir = os.path.join(location, str(road.id))
    mkdir(road_sub_dir)
    receptor_df = generate_receptors_df_for_road(road)
    road_df = road_to_dataframe(road)
    print road_sub_dir
    for (i, combination) in enumerate(input_file_parameter_combinations()):
        run_dir = os.path.join(road_sub_dir, str(i))
        mkdir(run_dir)
        receptor_df.to_csv(os.path.join(run_dir, "receptors.csv"), index=False)
        road_df.to_csv(os.path.join(run_dir, "roads.csv"), index=False)
        generate_run_files(run_dir, road_df, combination)
    print "generated configurations for road ", road.id


@app.task
def run_model(run_type, location):
    subprocess.call([model_executable, run_type, location + "/"])


def binomial_coef(n, i):
    return np.product(range(1, n + 1)) / np.product(range(1, i + 1)) / np.product(range(1, n - i + 1))


def bernstein_polynomial(x, n, i):
    return binomial_coef(n, i) * (x ** i) * ((1 - x) ** (n - i))


def load_results_file(location):
    road_output_file = os.path.join(location, "results_CTOOLS_HOURLY_ROAD_Output.csv")
    rail_output_file = os.path.join(location, "results_CTOOLS_HOURLY_RAIL_Output.csv")
    area_output_file = os.path.join(location, "results_CTOOLS_HOURLY_AREA_Output.csv")
    point_output_file = os.path.join(location, "results_CTOOLS_HOURLY_POINT_Output.csv")
    sit_output_file = os.path.join(location, "results_CTOOLS_HOURLY_SIT_Output.csv")
    if os.path.isfile(road_output_file):
        return pandas.read_csv(road_output_file)
    elif os.path.isfile(rail_output_file):
        return pandas.read_csv(rail_output_file)
    elif os.path.isfile(area_output_file):
        return pandas.read_csv(area_output_file)
    elif os.path.isfile(point_output_file):
        return pandas.read_csv(point_output_file)
    elif os.path.isfile(sit_output_file):
        return pandas.read_csv(sit_output_file)
    else:
        raise ValueError("No results in specified location")


def generate_bezier_function(X, Y):
    def bezier_curve(x0, p1x, p1y, p2x, p2y):
        p0 = np.array([X[0], Y[0]])
        p1 = np.array([p1x, p1y])
        p2 = np.array([p2x, p2y])
        p3 = np.array([X[-1], Y[-1]])
        alpha0 = binomial_coef(3, 0)
        alpha1 = binomial_coef(3, 1)
        alpha2 = binomial_coef(3, 2)
        alpha3 = binomial_coef(3, 3)
        beta0 = X[0] * alpha0
        beta1 = p1x * alpha1
        beta2 = p2x * alpha2
        beta3 = X[-1] * alpha3
        gamma1 = beta2 - 3 * beta3
        gamma2 = beta1 - 2 * beta2 + 3 * beta3
        gamma3 = beta0 - beta1 + beta2 - beta3
        x1 = np.array([[newton(lambda t: gamma3 * t ** 3 + gamma2 * t ** 2 + gamma1 * t + beta3 - x, 0.5)] for x in x0])
        b0 = bernstein_polynomial(x1, 3, 0)
        b1 = bernstein_polynomial(x1, 3, 1)
        b2 = bernstein_polynomial(x1, 3, 2)
        b3 = bernstein_polynomial(x1, 3, 3)
        result = b0 * p0 + b1 * p1 + b2 * p2 + b3 * p3
        return result
    return bezier_curve


def fit_model_output(X, Y):
    bezier_curve = generate_bezier_function(X, Y)
    third = round(len(X) / 3)
    initial_values = [X[third], Y[third], X[2*third], Y[2*third]]
    (opts, cov) = curve_fit(bezier_curve, X, Y, initial_values)
    return bezier_curve, opts