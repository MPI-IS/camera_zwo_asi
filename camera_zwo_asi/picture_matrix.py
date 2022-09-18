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


def set_control(
        camera: Camera,
        parameter: str,
        value: int,
        timeout: float,
        threshold: float
)->None:
    camera.set_control(parameter,value)
    start = time.time()
    while time.time()-start < timeout:
        obtained_value = camera.get_controls()[parameter].value
        if abs(value-obtained_value)<threshold:
            return
        time.sleep(0.01)
    

def add_to_hdf5(
        camera: Camera,
        parameters: typing.Dict[str,int],
        hdf5_file: h5py.File,
        avg_over: int,
        previous_parameters: typing.Optional[typing.Dict[str,int]]=None
)->None:

    # setting the configuration
    for index, (parameter, value) in enumerate(parameters.items()):
        if previous_parameter is not None and previous_parameter[parameter]!=value:
            camera.set_control(parameter, value)

    # getting the configuration values, which may or may not
    # be what we asked for
    all_parameters = camera.get_controls() 
    current_parameters = OrderedDict()
    for parameter in parameters.keys():
        current_parameters[key] = all_parameters[parameter].value
    
    # taking and averaging the pictures
    images = [camera.capture() for _ in range(avg_over)]
    image = np.mean(images, axis=0)

    # adding the image to the hdf5 file
    group = hdf5_file
    for parameter, value in current_parameters.items():
        group = hdf5_file.require_group(str(value))
    group.create_dataset("image", data=image.get_data())

    # add the camera current configuration to the group
    group.attrs["camera_config"] = camera.to_toml()


def create_hdf5_library(
    camera: Camera, 
    parameters: typing.OrderedDict[str,ParameterRange],
    config: typing.Optional[typing.Union[Path,typing.Mapping[str,typing.Any]]],
    avg_over: int,
    hdf5_path: Path
)->:

    # opening the hdf5 file in write mode
    with h5py.File(hdf5_path, "w") as hdf5_file:
    
        # configuring the camera
        if config is not None:
            camera.configure_from_toml(config)

        # adding the parameters to the hd5 file
        data = repr(params)
        hdf5_file.attrs["parameters"] = data

        # iterating over all the parameters and adding
        # the images to the hdf5 file
        for values in iterate_parameters(params.values()):
            add_to_hdf5(
                camera, values,
                hdf5_file, avg_over=avg_over
            )
        
    
class ImageLibrary:

    def __init__(
            self,
            hdf5_path: Path
    ):
        self._hdf5_file = h5py.File(hdf5_path,"r")

        
