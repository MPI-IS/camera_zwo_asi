from collections import OrderedDict
import itertools
import alive_progress
from pathlib import Path
import time
import h5py
import typing
import numpy as np
from .camera import Camera
from .image import FlattenData
from .control_range import ControlRange


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


def estimate_total_duration(
    camera: Camera,
    control_ranges: OrderedDict[str, ControlRange],
    avg_over: int,
    exposure: typing.Optional[float] = None
) -> typing.Tuple[float, int]:
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
        exposure = camera.get_controls()["Exposure"].value / 1e6
        return len(all_controls) * avg_over * exposure, nb_pics

    return (sum([ac[exp_index] / 1e6 for ac in all_controls]) * avg_over, nb_pics)


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
    images: typing.List[FlattenData] = []
    for _ in range(avg_over):
        images.append(camera.capture().get_data())
        if progress:
            progress(exposure)
            if current_nb_pics is not None:
                current_nb_pics += 1
            else:
                current_nb_pics = 1
            print(f"taking pictures {current_nb_pics}/{total_nb_pics}")
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


def library(
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
    current_nb_pics: typing.Optional[int] = 0

    if progress:
        progress_class = alive_progress.alive_bar
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
