import typing
import toml
from pathlib import Path
from .camera import Camera
from .roi import ROI


class ControlRange:
    """
    Configuration item for the method "create_hdf5", allowing the user
    to specify for a given control which range of value should be used.

    Arguments
    ---------
    min:
      start of the range.
    max:
      end of the range.
    step:
      step between min and max.
    threshold:
      as the method 'create_hdf5' will go through the values, it
      will set the camera configuration accordingly. For some control
      (for now we only have temperature in mind) this may require time
      and not be precise. This threshold setup the accepted level of precision
      for the control.
    timeout:
      the camera will attempt to setup the right value (+/ threshold) for
      at maximum this duration (in seconds).
    """

    def __init__(
        self,
        min: int,
        max: int,
        step: int,
        threshold: int = 0,
        timeout: float = 0.1,
    ) -> None:
        self.min = min
        self.max = max
        self.step = step
        self.threshold = threshold
        self.timeout = timeout

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        attrs = ("min", "max", "step", "threshold", "timeout")
        return {attr: getattr(self, attr) for attr in attrs}

    def get_values(self) -> typing.List[int]:
        """
        return the list of values in the range
        """
        return list(range(self.min, self.max + 1, self.step))

    def __repr__(self) -> str:
        return str(
            f"ControlRange({self.min},{self.max}, "
            f"{self.step},{self.threshold},{self.timeout})"
        )

    @classmethod
    def from_toml(cls, path: Path) -> typing.Tuple[typing.Dict[str, object], ROI, int]:
        """
        Generate a list of instances of ControlRange, an instance
        of a ROI based on a toml configuration file and an int value setting
        how many pictures have to be taken per darkframe. The configuration
        files must have the keys "ROI", "controllables" and "average_over". The "ROI" section
        must have values for start_x, start_y, width, height, bins, type.
        Each controllable must have values for min, max, step, threshold and
        timeout (in seconds).
        """

        def _get_range(name: str, config: typing.Mapping[str, typing.Any]) -> object:
            required_keys = ("min", "max", "step", "threshold", "timeout")
            for rk in required_keys:
                if rk not in config.keys():
                    raise ValueError(
                        f"error with darkframes configuration file {path}, "
                        f"controllable {name}: "
                        f"missing required key '{rk}'"
                    )
            try:
                min_, max_, step, threshold, timeout = [
                    int(config[key]) for key in required_keys
                ]
            except ValueError as e:
                raise ValueError(
                    f"error with darkframes configuration file {path}, "
                    f"controllable {name}: "
                    f"failed to cast value to int ({e})"
                )
            return cls(min_, max_, step, threshold, timeout)

        if not path.is_file():
            raise FileNotFoundError(str(path))
        content = toml.load(str(path))

        required_keys = ("ROI", "average_over", "controllables")
        for rk in required_keys:
            if rk not in content.keys():
                raise ValueError(
                    f"error with darkframes configuration file {path}: "
                    f"missing key '{rk}'"
                )

        roi = typing.cast(ROI, ROI.from_toml(content["ROI"]))
        try:
            avg_over = int(content["average_over"])
        except ValueError as e:
            raise ValueError(
                f"failed to cast value for 'average_over' ({content['average_over']}) "
                f"to int: {e}"
            )

        controllables = content["controllables"]
        return (
            {name: _get_range(name, values) for name, values in controllables.items()},
            roi,
            avg_over,
        )

    @classmethod
    def generate_config_file(cls, camera: Camera, path: Path) -> None:
        """
        Generate a toml configuration file with reasonable
        default values. User can edit this file and then call
        the method 'from_toml' to get desired instances of ControlRange
        and ROI.
        """

        if not path.parent.is_dir():
            raise FileNotFoundError(
                f"can not generate the configuration file {path}: "
                f"directory {path.parent} not found"
            )
        r: typing.Dict[str, typing.Any] = {}
        roi = camera.get_roi().to_dict()
        r["ROI"] = roi
        control_ranges = {
            "Exposure": ControlRange(1000000, 30000000, 5000000, 1, 0.1),
            "TargetTemp": ControlRange(-15, 15, 3, 1, 30),
            "Gain": ControlRange(200, 400, 100, 1, 0.1),
        }
        r["controllables"] = {}
        for name, control_range in control_ranges.items():
            r["controllables"][name] = control_range.to_dict()
        with open(path, "w") as f:
            toml.dump(r, f)
