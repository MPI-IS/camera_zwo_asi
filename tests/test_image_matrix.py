import tempfile
import copy
import typing
import camera_zwo_asi as zwo
from pathlib import Path

class MockParameter:
    def __init__(self, value: int):
        self.value = value

class MockCamera:

    def __init__(self):
        self._values: typing.Dict[str,MockParameter] = {}

    def get_roi(self)->zwo.ROI:
        roi = zwo.ROI()
        roi.start_x = 0
        roi.start_y = 0
        roi.width = 100
        roi.height = 100
        roi.bins = 1
        roi.type = zwo.ImageType.raw8
        return roi
        
    def set_control(self,parameter:str,value:int):
        try:
            self._values[parameter].value = value
        except KeyError:
            param = MockParameter(value)
            self._values[parameter] = param
            
    def get_controls(self):
        return copy.deepcopy(self._values)

    def capture(self)->zwo.image.ImageRaw8:
        return zwo.image.ImageRaw8(100,100)

    def to_toml(self)->str:
        return repr(self._values)
    

def test_iterate_ints():

    a1 = [1,2,3]
    a2 = [4,5,6]
    a3 = [7,8,9]

    combins = list(zwo.image_matrix._iterate_ints(a1,a2,a3))

    assert len(combins) == 3*3*3

    assert (1,4,7) in combins
    assert (1,5,9) in combins
    assert (2,6,9) in combins
    assert (3,6,9) in combins
    assert (2,5,7) in combins
    assert (4,1,7) not in combins

def test_parameter_range_get_values():

    parameters = {
        "a":zwo.image_matrix.ParameterRange(0,10,5),
        "b":zwo.image_matrix.ParameterRange(0,3,1),
        "c":zwo.image_matrix.ParameterRange(0,15,3)
    }

    assert parameters["a"].get_values() == [0,5,10]
    assert parameters["b"].get_values() == [0,1,2,3]
    assert parameters["c"].get_values() == [0,3,6,9,12,15]

    
def test_image_matrix():

    camera = MockCamera()

    parameters = {
        "a":zwo.image_matrix.ParameterRange(0,10,5),
        "b":zwo.image_matrix.ParameterRange(0,3,1),
        "c":zwo.image_matrix.ParameterRange(0,6,3)
    }

    avg_over = 2
    
    with tempfile.TemporaryDirectory() as tmp:

        path = Path(tmp) / "test.hdf5"
        
        nb_images = zwo.image_matrix.create_hdf5(
            camera,
            parameters,
            avg_over,
            path,
        )

        assert nb_images == 3*4*3

