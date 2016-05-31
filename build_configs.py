import os
import models
import tasks
from common import mkdir


def generate_road_sets(location):
    road_dir = os.path.join(location, "roads")
    mkdir(location)
    mkdir(road_dir)
    roads = models.load_example_roads()
    for road in roads:
        tasks.generate_road_run_configurations.delay(road, road_dir)


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

