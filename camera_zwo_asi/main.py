"""
console scripts
"""

import os
import argparse
from pathlib import Path
from .camera import Camera
from camera_zwo_asi.bindings import get_nb_cameras, create_udev_file
from .control_range import ControlRange
from .create_library import library

_CONFIG_FILE = "zwo_asi.toml"

def execute(f: typing.Callable[[None],None])->typing.Callable[[None],None]:
    def run():
        print()
        try:
            f()
        except Exception as e:
            print(f"error:\n{e}\n")
            exit(1)
        print()
        exit(0)
        
def udev():
    """
    creates a files called 99-asi.rules and provides instruction on how to install it
    """
    create_udev_file()
    print("\nThe file 99-asi.rules has been created in the current directory.")
    print("You may install it: 'sudo install 99-asi.rules /lib/udev/rules.d'")
    print("and disconnect / reconnect the camera.")
    print(
        "More information: https://astronomy-imaging-camera.com/manuals/ASI%20Cameras%20software%20Manual%20Linux%20OSX%20EN.pdf\n"
    )

@execute
def print_():
    """
    print to the console information about the
    connected cameras
    """
    nb_cams = get_nb_cameras()
    for index in range(nb_cams):
        print(f"\n---- camera {index} ----")
        camera = Camera(index)
        print(camera)

@execute
def shot():
    """
    takes a picture using the camera, and optionaly
    saves it to a file and display it. If a file named 'zwo_asi.toml'
    is present in the current directory, the camera will first be configured
    using it. Call with '-help' for details.
    """

    parser = argparse.ArgumentParser("take pictures with a ZWO-ASI camera")

    # if several cameras are plugged, which to use ?
    parser.add_argument(
        "--index",
        type=int,
        required=False,
        help="index of the camera to use (0 if not specified)",
    )

    # do we save the image ?
    parser.add_argument(
        "--path",
        type=str,
        required=False,
        help="absolute path in which the image will be saved (not saved if not specified)",
    )

    # do we display the image ?
    parser.add_argument(
        "-silent",
        "--silent",
        action="store_true",
        help="if silent, the image will not be displayed",
    )

    # do we ignore present configuration file ?
    parser.add_argument(
        "-noconfig",
        "--noconfig",
        action="store_true",
        help="ignore the zwo_asi.toml file that may be present in the current directory",
    )

    args = parser.parse_args()

    # opening the camera
    if args.index:
        index = args.index
    else:
        index = 0
    print(f"opening camera {index}")
    camera = Camera(index)

    # is there a configuration file in the current directory?
    config_path = Path(os.getcwd()) / _CONFIG_FILE
    if config_path.is_file() and not args.noconfig:
        print(f"configuring using {config_path}")
        camera.configure_from_toml(config_path)

    # taking the picture
    print("taking picture")
    image = camera.capture()

    # saving the picture
    if args.path:
        save_path = Path(args.path)
        save_folder = save_path.parent
        if not save_folder.is_dir():
            raise FileNotFoundError(
                f"Can not save to {save_path}, no such folder: {save_folder}"
            )
        print(f"saving to {save_path}")
        image.save(save_path)

    # displaying the picture
    if not args.silent:
        print("displaying, press 'esc' to exit")
        image.display()


@execute
def dump():
    """
    Save the current camera's configuration to a file named 'zwo_asi.toml'
    """

    parser = argparse.ArgumentParser()

    # if several cameras are plugged, which to use ?
    parser.add_argument(
        "--index",
        type=int,
        required=False,
        help="index of the camera to use (0 if not specified)",
    )

    args = parser.parse_args()

    # opening the camera
    if args.index:
        index = args.index
    else:
        index = 0
    camera = Camera(index)

    # dumping the configuration
    path = Path(os.getcwd()) / _CONFIG_FILE
    camera.to_toml(path)

    print(f"configuration saved to {path}")



def _get_darkframes_path()->Path:
    path = Path(os.getcwd()) / "darkframes.toml"
    if not path.is_file():
        raise FileNotFoundError(
            "\ncould not find a file 'darkframes.toml' in the current "
            "directory. You may create one by calling zwo-asi-darkframes-config\n"
        )
    return path
    
@execute    
def darkframes_config():

    # opening the camera
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index",
        type=int,
        required=False,
        help="index of the camera to use (0 if not specified)",
    )
    args = parser.parse_args()
    if args.index:
        index = args.index
    else:
        index = 0
    camera = Camera(index)

    # path to configuration file
    path = _get_darkframes_path()
    
    # generating file with decent default values
    ControlRange.generate_config_file(camera, path)

    print(
        f"Generated the darkframes configuration file {path}.\n"
        "Edit and call zwo-asi-darkframes to generate the darkframes "
        "library file."
    )

    
@execute
def darkframes_library():

    # path to configuration file
    path = _get_darkframes_path()

    # reading configuration file
    control_ranges, roi, average_over = ControlRange.from_toml(path)

    # opening the camera
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index",
        type=int,
        required=False,
        help="index of the camera to use (0 if not specified)",
    )
    args = parser.parse_args()
    if args.index:
        index = args.index
    else:
        index = 0
    camera = Camera(index)
    camera.set_roi(roi)

    # creating library
    library(camera, control_ranges, average_over, path, progress=True)

    # informing user
    print(f"\ncreate the file {path}\n")


@execute
def darkframes_info():

    # path to configuration file
    path = _get_darkframes_path()

    library = Library(path)

    library_name = library.name()
    
    image_type = library.image_type().value
    width, height = library.size()
    control_ranges = library.params()

    nb_pics = 1
    for cr in control_ranges.values():
        nb_pics = nb_pics * len(cr.get_values())

    r = [
        str(
            f"Library: {library_name}\n"
            f"Image Library of {nb_pics} pictures.\n"
            f"image type: {image_type}\n"
            f"image size: {width}*{height}\n"
            f"parameters\n{'-'*10}"
        )
    ]

    for name,cr in control_ranges.items():
        r.append(str(cr,name))

    print()
    print "\n".join(r)
    print()

    
@execute
def darkframe_display():

    path = _get_darkframes_path()

    library = Library(path)
    controls = list(library.params().keys())
    
    parser = argparse.ArgumentParser()

    # each control parameter has its own argument
    for control on controls:
        parser.add_argument(
            f"--{control}",
            type=int,
            required=True,
            help="the value for the control"
        )

    # to make the image more salient
    parser.add_argument(
        f"--multiplier",
        type=float,
        required=False,
        default=1.,
        help="pixels values will be multiplied by it"
    )

    # optional resize
    parser.add_argument(
        f"--resize",
        type=float,
        required=False,
        default=1.,
        help="resize of the image during display"
    )

    
    args = parser.parse_args()

    control_values = {
        control: int(getattr(args,control))
        for control in controls
    }

    image, image_controls = library.get(control_values)
    
    if args.multiplier != 1.:
        image._data = image.get_data()*args.multiplier

    params = ", ".join([f"{control}: {value}" for control,value in image_controls.items()])
        
    image.display(label=params,resize=args.resize)
        
    
