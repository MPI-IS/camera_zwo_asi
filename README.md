
# CAMERA-ZWO-ASI

python wrapper over ZWO astronomical cameras

## What is it

camera-zwo-asi is a python wrapper of the C++ SDK as provided by [ZWO](https://astronomy-imaging-camera.com/). It provides a python object oriented interface for interacting with ZWO astronomical cameras. 
The version of SDK currently binded is 1.24.
You may find the original C++ SDK binaries and documentation [here](https://astronomy-imaging-camera.com/software-drivers).

## Requirements

camera-zwo-asi has been tested only with :

- python 3.10 on Ubuntu 20.04
- python 3.9 on raspberry pi 3 (PI OS Lite 32-bit) 

but is likely to work with other recent version of python3 / ubuntu / raspberry. Compilation on other linux based platforms is less likely to be successful. 

### Dependencies

The following APT dependencies are required:

```bash
apt install -y libusb-1.0-0-dev libgl1-mesa-glx  libglib2.0-dev libopencv-dev python3-dev cmake ninja-build libusb-dev
```

For raspberry, also install:

```
apt install -y libatlas-base-dev
```

## Installation

### from PyPI

```bash
pip install camera-zwo-asi
```

### from source

```bash
git clone https://github.com/MPI-IS/camera_zwo_asi.git
cd camera_zwo_asi
pip install .
```

### allow your computer to reach your USB camera

Run:

```bash
zwo-asi-udev
```

and follow the instruction printed on screen.

### running unit-tests

Tests requires to have a usb camera plugged in.
After installation from source:

```
cd camera_zwo_asi
pytest ./tests/test.py
```

## Command line usage

The following command line tools are provided:

### Information about connected camera(s)

```bash
# will print information about connected cameras
zwo-asi-print
```

### Dumping the current configuration of the camera

```bash
# will create in the current folder a file called 'zwo_asi.toml' which
# contains the current configuration of the camera
zwo-asi-dump
```

### Taking pictures

```bash
# Takes a picture and display it. If there is a file 'zwo-asi.toml' in the current
# directory, configure first the camera using it.
zwo-asi-shot

# Same as above, but does not display the image.
zwo-asi-shot -silent

# Same as above, and also save the file to /tmp/img.bmp
# For the list of supported file formats:
# https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#imread
zwo-asi-shot -silent --path /tmp/img.bmp

# Same as above, but ignores the 'zwo-asi.toml' file that may be in the
# current directory.
zwo-asi-shot -silent -noconfig --path /tmp/img.bmp

# Same as above, but uses the second camera (index 1).
# Will work only if at least two cameras are connected.
zwo-asi-shot -silent -noconfig --path /tmp/img.bmp --index 1

# Getting info:
zwo-asi-shot -h
```

### Taking pictures with the configuration of your choice

``` bash
# generate the file corresponding to the current camera's configuration
zwo-asi-dump

#
# edit zwo_asi.toml to your liking. 
#

# take a picture with your desired configuration
zwo-asi-shot
```

When setting up the configuration (by editing ```zwo_asi.toml```), some controllable supports 'auto mode' and some are not writable. When calling ```zwo-asi-print```, you may see which ones, by looking at the column 'auto-mode' and 'writable'. For example:

```
(asi sdk: 1, 24, 0, 0)
ZWO ASI294MC Pro (id: 0)
max heigth: (2822) | max width: (4144) |
colored: * | mechanical shuttger: - | st4 port: - | 
has cooler: * | is usb3 host: * | is usb3: * | 
is triggered camera: - | bayer pattern: RG
supported bins: 1 2 3 4 
supported image types: raw8 rgb24 raw16 y8 
pixel size (um): 4.63 | elec per ADU: 0.399 | bit depth: 14

|controllable               |value   |min value |max value    |auto-mode  |in auto-mode  |writable
--
|AutoExpMaxExpMS            |30000   |1         |60000        |           |              |*
|AutoExpMaxGain             |285     |0         |570          |           |              |*
|AutoExpTargetBrightness    |100     |50        |160          |           |              |*
|BandWidth                  |80      |40        |100          |*          |*             |*
|CoolPowerPerc              |0       |0         |100          |           |              | 
|CoolerOn                   |0       |0         |1            |           |              |*
|Exposure                   |10000   |32        |2000000000   |*          |              |*
|Flip                       |0       |0         |3            |           |              |*
|Gain                       |200     |0         |570          |*          |              |*
|HighSpeedMode              |0       |0         |1            |           |              |*
|MonoBin                    |0       |0         |1            |           |              |*
|Offset                     |8       |0         |80           |           |              |*
|TargetTemp                 |0       |-40       |30           |           |              |*
|Temperature                |0       |-500      |1000         |           |              | 
|WB_B                       |95      |1         |99           |*          |              |*
|WB_R                       |52      |1         |99           |*          |              |*
```

```BandWidth``` supports auto-mode and is currently in auto-mode, ```Exposure``` supports auto-mode
but is not currently in auto-mode. Temperature is not writable.

To set in ```zwo_asi.toml``` a controllable in auto mode, use the string "auto". For example, this sets BandWidth to auto-mode:

```
[controllables]
AutoExpMaxExpMS = 30000
AutoExpMaxGain = 285
AutoExpTargetBrightness = 100
BandWidth = "auto"
CoolerOn = 0
Exposure = 10000
Flip = 0
Gain = 200
HighSpeedMode = 0
MonoBin = 0
Offset = 8
TargetTemp = 0
WB_B = 95
WB_R = 52
```

There are also a few rules that has to be respected when setting the values of the ROI (Region Of Interest):

- the width and height are positive, and below the max allowed values
- the width must be a multiple of 8
- the height must be a multiple of 2
- binned sensor width and height must be respected
       (i.e. start_x + width < max_width / number bins; and
        start_y + height < max_height / number_bins)

For example, this respects these rules:

```
[roi]
start_x = 0
start_y = 0
width = 4144
height = 2822
bins = 1
type = "raw8"
```

*note:*

when the camera closes, it restores its configuration. Therefore calling ```zwo-asi-print``` after taking a picture with ```zwo-asi-shot``` may not display the configuration that was used to take the picture. 

## API usage

```python
from pathlib import Path
import camera_zwo_asi

# connecting to the camera
# at index 0
camera = camera_zwo_asi.Camera(0)

# printing information in the
# terminal
print(camera)

# changing some controllables
# (supported arguments: the one that are
# indicated as 'writable' in the information
# printed above)
camera.set_control("Gain",300)
camera.set_control("Exposure","auto")

# changing the ROI (region of interest)
roi = camera.get_roi()
roi.type = camera_zwo_asi.ImageType.rgb24
roi.start_x = 20
roi.start_y = 20
roi.bins = 2
roi.width = 480
roi.height = 340
camera.set_roi(roi)

# saving this updated configuration to a file
conf_path = Path("/tmp") / "asi.toml"
camera.to_toml(conf_path)

# taking the picture
filepath = Path("/tmp") / "asi.bmp"
show = True
# filepath and show are optional, if you do not
# want to save the image or display it
image = camera.capture(filepath=filepath,show=show)

# getting a flat numpy array with the image data
image.get_data()

# getting a shaped numpy array with image data
image.get_image()

# showing the image
image.display(resize=0.25)

# saving the image (once more, for demo)
image.save(filepath)

# configuring the camera using a configuration file
camera.configure_from_toml(conf_path)

# taking a picture, overwriting the previous image
camera.capture(image=image)
image.display(resize=1.5)
```

## Other project

[python-zwoasi](https://github.com/python-zwoasi/python-zwoasi) is another python wrapper for ZWO cameras.

## Author and copyright

Vincent Berenz, Max Planck Institute for Intelligent Systems, Empirical Inference Department

Copyright 2022 Max Planck Gesellschaft
