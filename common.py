import os


def mkdir(dir_name):
    try:
        os.mkdir(dir_name)
    except OSError as err:
        if not err.errno == 17:
            raise