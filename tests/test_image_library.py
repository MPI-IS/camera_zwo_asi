import tempfile
import copy
import typing
import camera_zwo_asi as zwo
from pathlib import Path


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
        return zwo.image.ImageRaw8(100, 100)

    def to_toml(self) -> str:
        return repr({k: v.value for k, v in self._values.items()})


def test_iterate_ints():

    a1 = [1, 2, 3]
    a2 = [4, 5, 6]
    a3 = [7, 8, 9]

    combins = list(zwo.create_library._iterate_ints(a1, a2, a3))

    assert len(combins) == 3 * 3 * 3

    assert (1, 4, 7) in combins
    assert (1, 5, 9) in combins
    assert (2, 6, 9) in combins
    assert (3, 6, 9) in combins
    assert (2, 5, 7) in combins
    assert (4, 1, 7) not in combins


def test_control_range_get_values():

    controls = {
        "a": zwo.create_library.ControlRange(0, 10, 5),
        "b": zwo.create_library.ControlRange(0, 3, 1),
        "c": zwo.create_library.ControlRange(0, 15, 3),
    }

    assert controls["a"].get_values() == [0, 5, 10]
    assert controls["b"].get_values() == [0, 1, 2, 3]
    assert controls["c"].get_values() == [0, 3, 6, 9, 12, 15]


def test_create_library():

    camera = MockCamera()

    controls = {
        "a": zwo.create_library.ControlRange(0, 10, 5),
        "b": zwo.create_library.ControlRange(0, 3, 1),
        "c": zwo.create_library.ControlRange(0, 6, 3),
    }

    avg_over = 2

    with tempfile.TemporaryDirectory() as tmp:

        path = Path(tmp) / "test.hdf5"

        nb_images = zwo.library(camera, controls, avg_over, path, progress=False)

        assert nb_images == 3 * 4 * 3

        with zwo.ImageLibrary(path) as il:

            params = il.params()
            assert params["a"].min == 0
            assert params["b"].max == 3
            assert params["c"].step == 3

            desired = {"a": 5, "b": 1, "c": 6}
            image, camera_config = il.get(desired)
            assert camera_config["a"] == 5
            assert camera_config["b"] == 1
            assert camera_config["c"] == 6

            desired = {"a": 1, "b": 1, "c": 6}
            image, camera_config = il.get(desired)
            assert camera_config["a"] == 0
            assert camera_config["b"] == 1
            assert camera_config["c"] == 6

            desired = {"a": -1, "b": 1, "c": 6}
            image, camera_config = il.get(desired)
            assert camera_config["a"] == 0
            assert camera_config["b"] == 1
            assert camera_config["c"] == 6

            desired = {"a": 8, "b": 2, "c": 5}
            image, camera_config = il.get(desired)
            assert camera_config["a"] == 10
            assert camera_config["b"] == 2
            assert camera_config["c"] == 6

            desired = {"a": -1, "b": 1, "c": 1}
            image, camera_config = il.get(desired)
            assert camera_config["a"] == 0
            assert camera_config["b"] == 1
            assert camera_config["c"] == 0

            new_image = camera.capture()

            try:
                new_image.get_data() - image.get_data()
            except Exception as e:
                assert False, str(
                    f"substracting an image from the library "
                    f"to a new image raised an exception: {e}"
                )


def test_create_library_with_exposure():

    camera = MockCamera()

    controls = {
        "a": zwo.create_library.ControlRange(0, 10, 5),
        "Exposure": zwo.create_library.ControlRange(1000, 2000, 500),
        "c": zwo.create_library.ControlRange(0, 6, 3),
    }

    avg_over = 2

    with tempfile.TemporaryDirectory() as tmp:

        path = Path(tmp) / "test.hdf5"

        nb_images = zwo.library(camera, controls, avg_over, path, progress=False)
