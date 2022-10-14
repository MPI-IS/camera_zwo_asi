from collections import OrderedDict
import copy
import itertools
from pathlib import Path
import toml
import time
import h5py
import typing
import numpy as np
from .roi import ROI
from .camera import Camera
from .image import get_image_class, Image, FlattenData
from camera_zwo_asi.bindings import ImageType


class ControlRange:
    """
    Configuration item for the method "create_hdf5", allowing the user
    to specify for a given control which range of value should be used.

    Arguments
    ---------
    min:
      start of the range.
    max:
      end of the range.
    step:
      step between min and max.
    threshold:
      as the method 'create_hdf5' will go through the values, it
      will set the camera configuration accordingly. For some control
      (for now we only have temperature in mind) this may require time
      and not be precise. This threshold setup the accepted level of precision
      for the control.
    timeout:
      the camera will attempt to setup the right value (+/ threshold) for
      at maximum this duration (in seconds).
    """

    def __init__(
        self,
        min: int,
        max: int,
        step: int,
        threshold: int = 0,
        timeout: float = 0.1,
    ) -> None:
        self.min = min
        self.max = max
        self.step = step
        self.threshold = threshold
        self.timeout = timeout

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        attrs = ("min", "max", "step", "threshold", "timeout")
        return {attr: getattr(self, attr) for attr in attrs}

    def get_values(self) -> typing.List[int]:
        """
        return the list of values in the range
        """
        return list(range(self.min, self.max + 1, self.step))

    def __repr__(self) -> str:
        return str(
            f"ControlRange({self.min},{self.max}, "
            f"{self.step},{self.threshold},{self.timeout})"
        )

    @classmethod
    def from_toml(cls, path: Path) -> typing.Tuple[typing.Dict[str, object], ROI, int]:
        """
        Generate a list of instances of ControlRange, an instance
        of a ROI based on a toml configuration file and an int value setting
        how many pictures have to be taken per darkframe. The configuration
        files must have the keys "ROI", "controllables" and "average_over". The "ROI" section
        must have values for start_x, start_y, width, height, bins, type.
        Each controllable must have values for min, max, step, threshold and
        timeout (in seconds).
        """

        def _get_range(name: str, config: typing.Mapping[str, typing.Any]) -> object:
            required_keys = ("min", "max", "step", "threshold", "timeout")
            for rk in required_keys:
                if rk not in config.keys():
                    raise ValueError(
                        f"error with darkframes configuration file {path}, "
                        f"controllable {name}: "
                        f"missing required key '{rk}'"
                    )
            try:
                min_, max_, step, threshold, timeout = [
                    int(config[key]) for key in required_keys
                ]
            except ValueError as e:
                raise ValueError(
                    f"error with darkframes configuration file {path}, "
                    f"controllable {name}: "
                    f"failed to cast value to int ({e})"
                )
            return cls(min_, max_, step, threshold, timeout)

        if not path.is_file():
            raise FileNotFoundError(str(path))
        content = toml.load(str(path))

        required_keys = ("ROI", "average_over", "controllables")
        for rk in required_keys:
            if rk not in content.keys():
                raise ValueError(
                    f"error with darkframes configuration file {path}: "
                    f"missing key '{rk}'"
                )

        roi = typing.cast(ROI, ROI.from_toml(content["ROI"]))
        try:
            avg_over = int(content["average_over"])
        except ValueError as e:
            raise ValueError(
                f"failed to cast value for 'average_over' ({content['average_over']}) "
                f"to int: {e}"
            )

        controllables = content["controllables"]
        return (
            {name: _get_range(name, values) for name, values in controllables.items()},
            roi,
            avg_over,
        )

    @classmethod
    def generate_config_file(cls, camera: Camera, path: Path) -> None:
        """
        Generate a toml configuration file with reasonable
        default values. User can edit this file and then call
        the method 'from_toml' to get desired instances of ControlRange
        and ROI.
        """

        if not path.parent.is_dir():
            raise FileNotFoundError(
                f"can not generate the configuration file {path}: "
                f"directory {path.parent} not found"
            )
        r: typing.Dict[str, typing.Any]
        roi = camera.get_roi().to_dict()
        r["ROI"] = roi
        control_ranges = {
            "Exposure": ControlRange(1000000, 30000000, 5000000, 1, 0.1),
            "TargetTemp": ControlRange(-15, 15, 3, 1, 30),
            "Gain": ControlRange(200, 400, 100, 1, 0.1),
        }
        r["controllables"] = {}
        for name, control_range in control_ranges.items():
            r["controllables"][name] = control_range.to_dict()
        with open(path, "w") as f:
            toml.dump(r, f)


def _iterate_ints(*a) -> typing.Generator[typing.Tuple[int, ...], None, None]:
    """
    returns all combination of values
    """
    for values in itertools.product(*a):
        yield values
    return None


def _iterate_controls(
    controls: typing.List[ControlRange],
) -> typing.Generator[typing.Tuple[int, ...], None, None]:
    """
    Function that iterate over all the possible combinations of
    controls
    """
    all_values = [prange.get_values() for prange in controls]
    return _iterate_ints(*all_values)


def _get_measure_control(camera: Camera, control: str) -> int:
    if control == "TargetTemp":
        return int(camera.get_controls()["Temperature"].value / 10.0 + 0.5)
    return camera.get_controls()[control].value


def _set_control(
    camera: Camera, control: str, value: int, timeout: float, threshold: float
) -> None:
    """
    Configure the camera.
    """
    camera.set_control(control, value)
    start = time.time()
    while time.time() - start < timeout:
        obtained_value = _get_measure_control(camera, control)
        if abs(value - obtained_value) <= threshold:
            return
        time.sleep(0.01)


def _estimate_duration(
    controls: typing.Dict[str, int], exposure: typing.Optional[float] = None
) -> float:
    try:
        duration = controls["Exposure"] / 1e6
    except KeyError:
        duration = exposure
    return duration


def estimate_total_duration(
    camera: Camera,
    control_ranges: OrderedDict[str, ControlRange],
    avg_over: int,
) -> typing.Tuple[int, int]:
    """
    Return an estimation of how long capturing all darkframes will
    take (in seconds). If "Exposure" is in the control range,
    then the corresponding values will be used for the evaluation.
    Else, 'exposure' should not be None.

    Returns
    -------
       the expected duration (in seconds) and the number of pictures
       that will be taken.
    """

    controls = list(control_ranges.keys())
    if "Exposure" in controls:
        exp_index = controls.index("Exposture")
    else:
        exp_index = None

    all_controls = list(
        _iterate_controls([control_ranges[control] for control in controls])
    )

    nb_pics = len(all_controls) * avg_over

    if exp_index is None:
        return len(all_controls) * avg_over * exposure, nb_pics

    exposure = camera.get_controls()["Exposure"].value

    return (
        sum([ac[exp_index] / 1e6 for ac in all_controls]) * avg_over * exposure,
        nb_pics,
    )


def _add_to_hdf5(
    camera: Camera,
    controls: typing.Dict[str, int],
    hdf5_file: h5py.File,
    avg_over: int,
    timeouts: typing.List[float],
    thresholds: typing.List[int],
    previous_controls: typing.Optional[typing.Dict[str, int]] = None,
    progress: typing.Optional[alive_progress.core.progress.__AliveBarHandle] = None,
    current_nb_pics: typing.Optional[int] = None,
    total_nb_pics: typing.Optional[int] = None,
) -> typing.Optional[int]:
    """
    Has the camera take images, average them and adds this averaged image
    to the hdf5 file, with 'path'
    like hdf5_file[param1.value][param2.value][param3.value]...
    Before taking the image, the camera's configuration is set accordingly.
    """

    if "Exposure" not in controls.keys():
        exposure = camera.get_controls()["Exposure"].value / 1e6
    else:
        exposure = controls["Exposure"] / 1e6

    # setting the configuration
    for index, (control, value) in enumerate(controls.items()):
        if previous_controls is None or previous_controls[control] != value:
            _set_control(camera, control, value, timeouts[index], thresholds[index])

    # getting the configuration values, which may or may not
    # be what we asked for (e.g. when setting temperature)
    all_controls = camera.get_controls()
    current_controls = OrderedDict()
    for control in controls.keys():
        current_controls[control] = all_controls[control].value

    # taking and averaging the pictures
    images = []
    for _ in range(avg_over):
        images.append[camera.capture().get_data()]
        if progress:
            progress(exposure)
            try:
                current_nb_pics += 1
            except:
                current_nb_pics = 1
            printf(f"taking pictures {current_nb_pics}/{total_nb_pics}")
    image = np.mean(images, axis=0)

    # adding the image to the hdf5 file
    group = hdf5_file
    for control, value in current_controls.items():
        group = group.require_group(str(value))
    group.create_dataset("image", data=image)

    # add the camera current configuration to the group
    group.attrs["camera_config"] = camera.to_toml()

    return current_nb_pics


class _no_progress:
    def __init__(self, _, dual_line=None, title=None):
        pass

    def __enter__(self):
        return None

    def __exit__(self, _, __, ___):
        pass


def create_hdf5(
    camera: Camera,
    controls: OrderedDict[str, ControlRange],
    avg_over: int,
    hdf5_path: Path,
    progress: bool = True,
) -> int:
    """
    Create an hdf5 image library file, by taking pictures using
    the specified configuration range. For each configuration,
    'avg_over' pictures are taken and averaged.
    Images can be accessed using instances of 'ImageLibrary'.
    """

    total_duration, total_nb_pics = estimate_total_duration(camera, controls, avg_over)
    current_nb_pics = 0

    if progress:
        progress_class = alive_bar
    else:
        progress_class = _no_progress

    with progress_class(
        total_duration, dual_line=True, title="image database creation"
    ) as progress_bar:

        timeouts = [control.timeout for control in controls.values()]
        thresholds = [control.threshold for control in controls.values()]

        # opening the hdf5 file in write mode
        with h5py.File(hdf5_path, "w") as hdf5_file:

            # adding the controls to the hdf5 file
            hdf5_file.attrs["controls"] = repr(controls)

            # adding the file format, width and height to the hdf5 file
            roi = camera.get_roi()
            hdf5_file.attrs["image_type"] = str(roi.type)
            hdf5_file.attrs["width"] = roi.width
            hdf5_file.attrs["height"] = roi.height

            # counting the number of images saved
            nb_images = 0

            # iterating over all the controls and adding
            # the images to the hdf5 file
            control_ranges: typing.List[ControlRange] = list(controls.values())
            for values in _iterate_controls(control_ranges):
                values_dict = {
                    control: value for control, value in zip(controls.keys(), values)
                }
                current_nb_pics = _add_to_hdf5(
                    camera,
                    values_dict,
                    hdf5_file,
                    avg_over,
                    timeouts,
                    thresholds,
                    progress=progress_bar,
                    current_nb_pics=current_nb_pics,
                    total_nb_pics=total_nb_pics,
                )
                nb_images += 1

    return nb_images


def _get_closest(value: int, values: typing.List[int]) -> int:
    """
    Returns the item of values the closest to value
    (e.g. value=5, values=[1,6,10,11] : 6 is returned)
    """
    diffs = [abs(value - v) for v in values]
    index_min = min(range(len(diffs)), key=diffs.__getitem__)
    return values[index_min]


def _get_image(
    values: typing.List[int], hdf5_file: h5py.File, index: int = 0
) -> typing.Tuple[FlattenData, typing.Dict]:
    """
    Returns the image in the library which has been taken with
    the configuration the closest to "values".
    """

    if "image" in hdf5_file.keys():
        img = hdf5_file["image"]
        config = eval(hdf5_file.attrs["camera_config"])
        return img, config

    else:
        keys = list([int(k) for k in hdf5_file.keys()])
        best_value = _get_closest(values[index], keys)
        return _get_image(values, hdf5_file[str(best_value)], index + 1)


class ImageLibrary:
    """
    Object for reading an hdf5 file that must have been generated
    using the 'create_hdf5' method of this module.
    Allows to access images in the library.
    """

    def __init__(self, hdf5_path: Path) -> None:
        self._path = hdf5_path
        self._hdf5_file = h5py.File(hdf5_path, "r")
        self._controls: typing.List[str] = sorted(
            eval(self._hdf5_file.attrs["controls"])
        )
        self._type: ImageType = eval(self._hdf5_file.attrs["image_type"])
        self._width: int = int(self._hdf5_file.attrs["width"])
        self._height: int = int(self._hdf5_file.attrs["height"])
        self._image_class = get_image_class(self._type)

    def params(self) -> typing.OrderedDict[str, ControlRange]:
        """
        Returns the range of values that have been used to generate
        this file.
        """
        return eval(self._hdf5_file.attrs["controls"])

    def image_type(self) -> ImageType:
        """
        The type of the images stored in the library
        """
        return self._type

    def size(self) -> typing.Tuple[int, int]:
        """
        Width and height of the images stored in the library
        """
        return (self._width, self.height)

    def get(self, controls: typing.Dict[str, int]) -> typing.Tuple[Image, typing.Dict]:
        """
        Returns the image in the library that was taken using
        the configuration the closest to the passed controls.

        Arguments
        ---------
        controls:
          keys of controls are expected to the the same as
          the keys of the dictionary returned by the method
          'params' of this class

        Returns
        -------
        Tuple: image of the library and its related camera configuration
        """

        for control in controls:
            if control not in self._controls:
                slist = ", ".join(self._controls)
                raise ValueError(
                    f"Failed to get an image from the image library {self._path}: "
                    f"the control {control} is not supported (supported: {slist})"
                )

        for control in self._controls:
            if control not in controls:
                raise ValueError(
                    f"Failed to get an image from the image library {self._path}: "
                    f"the value for the control {control} needs to be specified"
                )

        values = list(controls.values())
        image: FlattenData
        config: typing.Dict
        image, config = _get_image(values, self._hdf5_file, index=0)
        image_instance = self._image_class(self._width, self._height)
        image_instance._data = image
        return image_instance, config

    def close(self) -> None:
        self._hdf5_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
