import typing
import h5py
from .image import (
    FlattenData,
    ImageType,
    Image,
    get_image_class
)
from pathlib import Path
from .control_range import ControlRange


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
        return (self._width, self._height)

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
