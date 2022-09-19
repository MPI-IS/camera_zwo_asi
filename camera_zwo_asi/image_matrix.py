from collections import OrderedDict
import copy
import itertools
from pathlib import Path
import time
import h5py
import typing
import numpy as np
from .camera import Camera
from .image import get_image_class, Image, FlattenData
from camera_zwo_asi.bindings import ImageType


class ParameterRange:
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

    def get_values(self) -> typing.List[int]:
        """
        return the list of values in the range
        """
        return list(range(self.min, self.max+1, self.step))

    def __repr__(self) -> str:
        return str(
            f"ParameterRange({self.min},{self.max}, "
            f"{self.step},{self.threshold},{self.timeout})"
        )


def _iterate_ints(*a)->typing.Generator[typing.Tuple[int,...],None,None]:
    for values in itertools.product(*a):
        yield values
    return None


def _iterate_parameters(
    parameters: typing.List[ParameterRange],
) -> typing.Generator[typing.Tuple[int,...], None, None]:
    """
    Function that iterate over all the possible combinations of
    parameters
    """
    all_values = [prange.get_values() for prange in parameters]
    return _iterate_ints(*all_values)


def _set_control(
    camera: Camera, parameter: str, value: int, timeout: float, threshold: float
) -> None:
    camera.set_control(parameter, value)
    start = time.time()
    while time.time() - start < timeout:
        obtained_value = camera.get_controls()[parameter].value
        if abs(value - obtained_value) <= threshold:
            return
        time.sleep(0.01)


def _add_to_hdf5(
    camera: Camera,
    parameters: typing.Dict[str, int],
    hdf5_file: h5py.File,
    avg_over: int,
    timeouts: typing.List[float],
    thresholds: typing.List[int],
    previous_parameters: typing.Optional[typing.Dict[str, int]] = None,
) -> None:

    # setting the configuration
    for index, (parameter, value) in enumerate(parameters.items()):
        if previous_parameters is None or previous_parameters[parameter] != value:
            _set_control(camera, parameter, value, timeouts[index], thresholds[index])

    # getting the configuration values, which may or may not
    # be what we asked for (e.g. when setting temperature)
    all_parameters = camera.get_controls()
    current_parameters = OrderedDict()
    for parameter in parameters.keys():
        current_parameters[parameter] = all_parameters[parameter].value

    # taking and averaging the pictures
    images = [camera.capture().get_data() for _ in range(avg_over)]
    image = np.mean(images, axis=0)

    # adding the image to the hdf5 file
    group = hdf5_file
    for parameter, value in current_parameters.items():
        group = group.require_group(str(value))
    group.create_dataset("image", data=image)

    # add the camera current configuration to the group
    group.attrs["camera_config"] = camera.to_toml()


def create_hdf5(
    camera: Camera,
    parameters: typing.OrderedDict[str, ParameterRange],
    avg_over: int,
    hdf5_path: Path
) -> int:

    timeouts = [parameter.timeout for parameter in parameters.values()]
    thresholds = [parameter.threshold for parameter in parameters.values()]
    
    # opening the hdf5 file in write mode
    with h5py.File(hdf5_path, "w") as hdf5_file:

        # adding the parameters to the hdf5 file
        hdf5_file.attrs["parameters"] = repr(parameters)

        # adding the file format, width and height to the hdf5 file
        roi = camera.get_roi()
        hdf5_file.attrs["image_format"] = str(roi.type)
        hdf5_file.attrs["width"] = str(roi.width)
        hdf5_file.attrs["height"] = str(roi.height)

        # counting the number of images saved
        nb_images = 0
        
        # iterating over all the parameters and adding
        # the images to the hdf5 file
        parameter_ranges: typing.List[ParameterRange] = list(parameters.values())
        for values in _iterate_parameters(parameter_ranges):
            values_dict = {
                parameter: value for parameter, value in zip(parameters.keys(), values)
            }
            _add_to_hdf5(camera, values_dict, hdf5_file, avg_over, timeouts, thresholds)
            nb_images+=1

        return nb_images

def _get_closest(value: int, values: typing.List[int]) -> int:
    diffs = [abs(value - v) for v in values]
    index_min = min(range(len(diffs)), key=diffs.__getitem__)
    return values[index_min]


def _get_image(
        values: typing.List[int],
        hdf5_file: h5py.File,
        index: int = 0
) -> typing.Tuple[FlattenData,typing.Dict]:

    keys = list([int(k) for k in hdf5_file.keys()])
    best_value = _get_closest(values[index], keys)

    if len(values) == (index - 2):
        group = hdf5_file[str(best_value)]
        img = group["image"]
        config = eval(group.attrs["camera_config"])
        return img,config

    return _get_image(values, hdf5_file[best_value], index + 1)


class ImageLibrary:
    def __init__(self, hdf5_path: Path) -> None:
        self._path = hdf5_path
        self._hdf5_file = h5py.File(hdf5_path, "r")
        self._parameters: typing.List[str] = sorted(
            eval(self._hdf5_file.attrs["parameters"])
        )
        type_: ImageType = eval(self._hdf5_file.attr["image_type"])
        width: int = int(self._hdf5_file.attr["width"])
        height: int = int(self._hdf5_file.attr["height"])
        image_class = get_image_class(type_)
        self._image_instance = image_class(width,height)
        
    def params(self) -> typing.OrderedDict[str, ParameterRange]:
        return eval(self._hdf5_file.attrs["parameters"])

    def get(
            self,
            parameters: typing.Dict[str, int]
    ) -> typing.Tuple[Image,typing.Dict]:

        for parameter in parameters:
            if parameter not in self._parameters:
                slist = ", ".join(self._parameters)
                raise ValueError(
                    f"Failed to get an image from the image library {self._path}: "
                    f"the parameter {parameter} is not supported (supported: {slist})"
                )

        for parameter in self._parameters:
            if parameter not in parameters:
                raise ValueError(
                    f"Failed to get an image from the image library {self._path}: "
                    f"the value for the parameter {parameter} needs to be specified"
                )

        values = list(parameters.values())
        image: FlattenData = _get_image(values, self._hdf5_file, index=0)
        self._image_instance._data = image
        return copy.deepcopy(self._image_instance)
        
    def close(self) -> None:
        self._hdf5_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
