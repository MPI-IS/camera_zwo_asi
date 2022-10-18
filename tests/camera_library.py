from collections import OrderedDict
from pathlib import Path
import camera_zwo_asi as zwo

gain_range = zwo.ControlRange(300, 570, 100)
exposure_range = zwo.ControlRange(int(1 * 1e6), int(30 * 1e6), int(5 * 1e6))

ranges = OrderedDict()
ranges["Gain"] = gain_range
ranges["Exposure"] = exposure_range

average_over = 3


def build_library(path: Path) -> None:

    camera = zwo.Camera(0)

    zwo.library(camera, ranges, average_over, path, progress=True)


if __name__ == "__main__":

    build_library(Path("/tmp/camera_library_test.hdf5"))
