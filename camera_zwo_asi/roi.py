import toml
import typing
import numpy as np
from pathlib import Path
from camera_zwo_asi import bindings
from .image import FlattenData, ImageData, Image, get_image


class ROI(bindings.ROI):
    """
    Region Of Interest.

    Attributes:
      start_x: pixels
      start_y: pixels
      width: pixels
      height: pixels
      bins: number of bins
      type: image type (raw8, rgb24, raw16 or y8)
    """

    def __init__(self):
        super().__init__()

    def get_image(self) -> Image:
        """
        Returns an image of the correct size, based on the ROI
        width, heigth and image type.
        """
        return get_image(self.type, self.width, self.height)

    @classmethod
    def from_toml(
        cls, content: typing.Union[Path, typing.Dict[str, typing.Any]]
    ) -> object:
        """
        Instantiate ROI, based on either the path to a TOML file, or via
        a dictionary.
        """

        d: typing.Dict[str, typing.Any]

        if isinstance(content, Path):
            if not content.is_file():
                raise FileNotFoundError(
                    f"failed to create an instance of ROI from {path}: file not found"
                )
            d = toml.load(content)
        else:
            d = content

        required_keys = ("start_x", "start_y", "width", "height", "bins", "type")
        missing_keys = [rk for rk in required_keys if not rk in d]
        if missing_keys:
            missing_str = ", ".join(missing_keys)
            raise ValueError(
                f"failed to create an instance of ROI: missing configuration for "
                f"{missing_str}"
            )

        roi = cls()
        for rk in required_keys:
            if rk == "type":
                image_type = bindings.ImageType.__members__[d[rk]]
                roi.type = image_type
            else:
                setattr(roi, rk, d[rk])

        return roi

    def check(self, info: bindings.CameraInfo) -> typing.List[str]:
        """
        Checks if this instance of ROI can be used to configure a camera
        (based on the information of the camera, method Camera.get_info).
        An instance is suitable if:
        - the image type is supported by the camera
        - the number of bins is supported by the camera
        - the width and height are positive, and below the max allowed values
        - the width must be a multiple of 8
        - the height must be a multiple of 2
        - binned sensor width and height must be respected
          (i.e. start_x + width < max_width / number bins; and
           start_y + height < max_height / number_bins)

        Arguments:
          info: as returned by the method Camera.get_info

        Returns:
          A list of issues. An empty list means the ROI can be used
          to configurare the camera.

        """

        issues: typing.List[str] = []

        if self.bins not in info.supported_bins:
            supported_bins: str = ",".join([str(b) for b in info.supported_bins])
            issues.append(
                "{} bin(s) not supported (supported: {})".format(
                    self.bins, supported_bins
                )
            )

        if self.type not in info.supported_image_types:
            supported_types: str = ",".join(
                [str(t) for t in info.supported_image_types]
            )
            issues.append(
                "Image type {} not supported (supported: {}".format(
                    image_type, supported_types
                )
            )

        if self.width < 0:
            issues.append("width can not be negative")

        if self.height < 0:
            issues.append("height can not be negative")

        if self.width > info.max_width:
            issues.append(
                f"width {self.width} is bigger than the maximal supported width {info.max_width}"
            )
        if self.height > info.max_height:
            issues.append(
                f"height {self.height} is bigger than the maximal supported height {info.max_height}"
            )
        if self.width % 8 != 0:
            issues.append(f"width {self.width} is not a multiple of 8")
        if self.height % 2 != 0:
            issues.append(f"height {self.height} is not a multiple of 2")

        if self.bins != 0:
            if self.start_x + self.width > (info.max_width / self.bins):
                raise ValueError(
                    "ROI and start position larger than binned sensor width"
                )
            if self.start_y + self.height > (info.max_height / self.bins):
                raise ValueError(
                    "ROI and start position larger than binned sensor height"
                )

        return issues

    def __str__(self):
        """
        Return a string informative about the values of the attributes.
        """

        return str(
            f"--ROI--\n"
            f"start x: {self.start_x}, start y: {self.start_y}\n"
            f"width: {self.width}, height: {self.height}\n"
            f"bins: {self.bin}, image type: {self.type}\n"
        )
