"""
console scripts
"""

import os
import argparse
from pathlib import Path
from .camera import Camera
from camera_zwo_asi.bindings import get_nb_cameras, create_udev_file

_CONFIG_FILE = "zwo_asi.toml"


def udev():
    """
    creates a files called 99-asi.rules and provides instruction on how to install it
    """
    create_udev_file()
    print("\nThe file 99-asi.rules has been created in the current directory.")
    print("You may install it: 'sudo install 99-asi.rules /lib/udev/rules.d'")
    print("and disconnect / reconnect the camera.")
    print("More information: https://astronomy-imaging-camera.com/manuals/ASI%20Cameras%20software%20Manual%20Linux%20OSX%20EN.pdf\n")

    
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


def _shot():
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


def shot():
    """
    takes a picture using the camera, and optionaly
    saves it to a file and display it. If a file named 'zwo_asi.toml'
    is present in the current directory, the camera will first be configured
    using it. Call with '-help' for details.
    """
    try:
        _shot()
    except Exception as e:
        print(f"\n[ERROR]: {e}\n")


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
