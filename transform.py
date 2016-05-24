import pandas
import math
import pyproj

_lambert = pyproj.Proj("+proj=lcc +lat_1=33 +lat_2=45 +lat_0=40 +lon_0=-97 +x_0=0 +y_0=0 +ellps=GRS80 "
                       "+datum=NAD83 +units=m +no_defs")


def latlong_dist(p0, p1):
    (p0_lon, p0_lat) = _lambert(p0[0], p0[1], inverse=True)
    (p1_lon, p1_lat) = _lambert(p1[0], p1[1], inverse=True)
    return math.sqrt((p1_lon - p0_lon) ** 2 + (p1_lat - p0_lat) ** 2)


def generate_receptors_for_line(startx, starty, endx, endy, num_receptors=50, receptor_offset=10):
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


def load_roads(road_file):
    roads_df = pandas.read_csv(road_file)
    roads = list(roads_df.itertuples())

