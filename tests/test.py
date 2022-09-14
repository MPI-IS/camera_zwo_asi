import toml
import typing
import pytest
import camera_zwo_asi
import tempfile
from pathlib import Path


def test_roi_from_dict():
    """
    Test ROI can be instantiated from dictionaries
    """
    
    # this should be a successfull instantiation
    d = {
        "start_x" : 0,
        "start_y" : 0,
        "width" : 100,
        "height" : 100,
        "bins" : 2,
        "type" : "raw8"
    }
    instance1 = camera_zwo_asi.ROI.from_toml(d)
    for attr in d.keys():
        if not attr == "type":
            assert getattr(instance1,attr) == d[attr]
    assert instance1.type== camera_zwo_asi.ImageType.raw8
    
    # failing instantiation: unknown image type
    with pytest.raises(Exception):
        d = {
            "start_x" : 0,
            "start_y" : 0,
            "width" : 100,
            "height" : 100,
            "bins" : 2,
            "type" : "stuff" # !
        }
        instance2 = camera_zwo_asi.ROI.from_toml(d)

    # failing instantiation: missing attribute
    with pytest.raises(Exception):
        d = {
            # "start_x" : 0, #!
            "start_y" : 0,
            "width" : 100,
            "height" : 100,
            "bins" : 2,
            "type" : "y8" 
        }
        instance2 = camera_zwo_asi.ROI.from_toml(d)

        
def test_roi_from_file():
    """
    Test ROI can be instantiated from a TOML file
    """
    
    # will be dump in the test toml file
    d = {
        "start_x" : 0,
        "start_y" : 0,
        "width" : 100,
        "height" : 100,
        "bins" : 2,
        "type" : "rgb24"
    }

    with tempfile.TemporaryDirectory() as tmp:

        path = Path(tmp) / "test.toml"

        # writing the ROI in a toml file
        with open(path,'w') as f:
            toml.dump(d,f)

        # instantiating from this file
        instance = camera_zwo_asi.ROI.from_toml(path)

        # checking all attribute values match the expected values
        for attr in d.keys():
            if not attr == "type":
                assert getattr(instance,attr) == d[attr]
        assert instance.type== camera_zwo_asi.ImageType.rgb24


def test_cam_config_to_toml():
    """
    Check camera's configuration can be dumped / read
    to / from TOML files
    """
    
    # connecting to the camera
    camera = camera_zwo_asi.Camera(0)

    # original configuration
    original_roi = camera.get_roi()
    original_controls = camera.get_controls()

    with tempfile.TemporaryDirectory() as tmp:

        f = Path(tmp) / "test.toml"

        # dumping configuration in a file
        camera.to_toml(f)

        # reconfiguring from this file
        camera.configure_from_toml(f)

    # checking nothing changed
    new_roi = camera.get_roi()
    new_controls = camera.get_controls()
    for attr in ("start_x", "start_y", "width", "height", "bins", "type"):
        assert getattr(original_roi,attr) == getattr(new_roi,attr)
    for controllable, instance in original_controls.items():
        if instance.is_writable:
            if instance.is_auto:
                assert new_controls[controllable].is_auto
            else:
                assert original_controls[controllable].value == new_controls[controllable].value 
        
    
def test_update_camera_config():

    # connecting to the camera
    camera = camera_zwo_asi.Camera(0)

    # original configuration
    roi = camera.get_roi()
    controls = camera.get_controls()

    # setting all values to non-auto min value
    for instance in controls.values():
        if instance.is_writable:
            instance.is_auto = False
            instance.value = instance.min_value

    # updating the configuration
    camera.configure(roi,controls)

    # did the update succeed ?
    for instance in camera.get_controls().values():
        if instance.is_writable:
            assert not instance.is_auto
            assert instance.value == instance.min_value
        
    # setting all values that can be auto to auto,
    # and all other values to mid value
    for instance in controls.values():
        if instance.supports_auto:
            instance.is_auto = True
        else:
            instance.value = int( (instance.max_value+instance.min_value) / 2. )
            
    # updating the configuration
    camera.configure(roi,controls)

    # did the update succeed ?
    for instance in camera.get_controls().values():
        if instance.is_writable:
            if instance.supports_auto:
                assert instance.is_auto
            else:
                assert instance.value == int( (instance.max_value+instance.min_value) / 2. )

