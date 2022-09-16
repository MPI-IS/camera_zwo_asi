from collections import OrderedDict
import itertools
from pathlib import Path
import hd5py
import typing
import numpy as np
from .camera import Camera
from .image import get_image_class

class ParameterRange:
    def __init__(self, min: int, max: int, step: int)->None:
        self.min = min
        self.max = max
        self.step = step

    def get_values(self)->typing.List[int]:
        """
        return the list of values in the range
        """
        return list(range(self.min, self.max, self.step))

    def next(self)->int:
        """
        function that yield the next value of the range
        """
        for value in range(self.min, self.max, self.step):
            yield value
        return None


def iterate_parameters(
    parameters: typing.List[ParameterRange]
)->typing.List[int]:
    """
    Function that iterate over all the possible combinations of
    parameters
    """
    all_values = [prange.get_values() for prange in parameters]
    for values in itertools.product(*all_values):
        yield values
    return None


def add_to_hdf5(
    camera: Camera,
    parameters: typing.Dict[str,int],
    hdf5_file: h5py.File,
    avg_over: int
)->None:

    # taking and averaging the pictures
    for parameter, value in parameters.items():
       camera.set_control(parameter, value)
    images = [camera.capture() for _ in range(avg_over)]
    image = np.mean(images, axis=0)

    # adding the image to the hdf5 file
    group = hdf5_file
    for parameter, value in parameters.items():
        group = hdf5_file.require_group(str(value))
    group.create_dataset("image", data=image.get_data())


def get_image_matrix(
    camera: Camera, 
    parameters: typing.OrderedDict[str,ParameterRange],
    config: typing.Optional[typing.Union[Path,typing.Mapping[str,typing.Any]]],
    hdf5_path: Path
)->:

    # opening the hdf5 file in write mode
    hdf5_file = h5py.File(hdf5_path, "w")
    
    # configuring the camera
    if config is not None:
        camera.configure_from_toml(config)

    # getting the image size
    roi = camera.get_roi()
    image_type = roi.type
    image_class = get_image_class(type)
    image = image_class(roi.width, roi.height)
    image_size = image.get_data_size()

    # iterating over all the parameters and adding
    # the images to the hdf5 file
    for values in iterate_parameters(parameters.values()):
        parameters = OrderedDict(zip(parameters.keys(), values))
        add_to_hdf5(camera, parameters, hdf5_file, avg_over=1)
        
    # closing the hdf5 file
    hdf5_file.close()
    