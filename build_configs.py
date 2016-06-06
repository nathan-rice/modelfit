import os
import models
import tasks
from common import mkdir


def generate_road_sets(location, local=False):
    road_dir = os.path.join(location, "roads")
    mkdir(location)
    mkdir(road_dir)
    roads = models.load_example_roads()
    for road in roads:
        if local:
            tasks.generate_road_run_configurations(road, road_dir)
        else:
            tasks.generate_road_run_configurations.delay(road, road_dir)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("location")
    parser.add_argument("--road", action="store_true")
    parser.add_argument("--local", action="store_true", default=False)
    args = parser.parse_args()
    if args.road:
        generate_road_sets(args.location, args.local)


if __name__ == "__main__":
    main()

