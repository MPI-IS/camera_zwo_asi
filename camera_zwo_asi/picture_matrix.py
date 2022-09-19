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
    # be what we asked for (e.g. when setting temperature)
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


def create_hdf5(
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
        data = repr(list(parameters.keys()))
        hdf5_file.attrs["parameters"] = data

        # iterating over all the parameters and adding
        # the images to the hdf5 file
        for values in iterate_parameters(params.values()):
            values_dict = {
                parameter:value
                for parameter,value
                in zip(parameters.keys(),values)
            }
            add_to_hdf5(
                camera, values,
                hdf5_file, avg_over=avg_over
            )


def _get_closest(value: int, values: typing.List[int])->int:
    diffs = [abs(value-v) for v in values]
    index_min = min(range(len(diffs)), key=diffs.__getitem__)
    return values[index_min]
    

def _get_image(
        values: typing.List[int],
        hdf5_file: h5py.File,
        index: int= 0
)->Image:

    keys = list([int(k) for k in hdf5_file.keys()])
    best_value = _get_closest(values[index],keys)
    
    if len(values)==(index-2):
        return hdf5_file[str(best_value)]

    return _get_image(
        values,
        hdf5_file[best_value],
        index+1
    )


class ImageLibrary:

    def __init__(
            self,
            hdf5_path: Path
    )->None:
        self._path = hdf5_path
        self._hdf5_file = h5py.File(hdf5_path,"r")
        self._parameters: typing.List[str] = sorted(eval(self._hdf5_file.attrs["parameters"]))

    def get(self,parameters: typing.Dict[str,int])->ImageData:

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
                
        values = self._parameters.values()
        
        return _get_image(
            values: typing.List[int],
            hdf5_file: self._h5py.File,
            index=0
        )
            
        
    def close(self)->None:
        self._hdf5_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()
