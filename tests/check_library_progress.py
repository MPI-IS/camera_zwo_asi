from collections import OrderedDict
from pathlib import Path
import time
import copy
import tempfile
import camera_zwo_asi as zwo


class MockControl:
    def __init__(self, value: int):
        self.value = value


class MockCamera:
    def __init__(self, default_exposure: float = 0.1):
        self._values: typing.Dict[str, MockControl] = {}
        self._values["Exposure"] = MockControl(default_exposure)

    def get_roi(self) -> zwo.ROI:
        roi = zwo.ROI()
        roi.start_x = 0
        roi.start_y = 0
        roi.width = 100
        roi.height = 100
        roi.bins = 1
        roi.type = zwo.ImageType.raw8
        return roi

    def set_control(self, control: str, value: int):
        try:
            self._values[control].value = value
        except KeyError:
            param = MockControl(value)
            self._values[control] = param

    def get_controls(self):
        return copy.deepcopy(self._values)

    def capture(self) -> zwo.image.ImageRaw8:
        try:
            exposure = self._values["Exposure"].value
            time.sleep(exposure / 1e6)
        except KeyError:
            pass
        return zwo.image.ImageRaw8(100, 100)

    def to_toml(self) -> str:
        return repr({k: v.value for k, v in self._values.items()})


def run():

    controls = OrderedDict()
    controls["a"] = zwo.ControlRange(1, 3, 1)
    controls["Exposure"] = zwo.ControlRange(500, 1000000, 1000000 - 500)
    controls["b"] = zwo.ControlRange(0, 20, 5)

    average_over = 5

    with tempfile.TemporaryDirectory() as tmp_dir:

        path = Path(tmp_dir) / "dummy_library.hdf5"

        zwo.library(MockCamera(), controls, average_over, path, progress=True)


if __name__ == "__main__":

    run()
