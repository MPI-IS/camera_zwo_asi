import copy
import typing
import cv2
import numpy as np
import nptyping as npt
from pathlib import Path
from camera_zwo_asi.bindings import ImageType

FlattenData = npt.NDArray[npt.Shape["1"], npt.UInt8]
UINT8ImageData = npt.NDArray[npt.Shape["*,*"], npt.UInt8]
UINT16ImageData = npt.NDArray[npt.Shape["*,*"], npt.UInt16]
UINT8RGBImageData = npt.NDArray[npt.Shape["*,*,3"], npt.UInt8]
ImageData = typing.Union[UINT8ImageData, UINT16ImageData, UINT8RGBImageData]


class Image:
    """
    Encapsulate data corresponding to an image, and provide convenience
    methods, e.g. for saving and displaying the image.
    This is an abstract class, a concrete subclass should be used.
    """

    def __init__(self, image_type: ImageType, width: int, height: int) -> None:

        self.image_type = image_type
        self.width = width
        self.height = height

    def get_data_size(self) -> int:
        """
        Size of the image, in bytes
        """
        raise NotImplementedError()

    def get_data(self) -> FlattenData:
        """
        Returns the raw data numpy array
        """
        raise NotImplementedError()

    def get_image(self) -> ImageData:
        """
        Returns the image numpy array, properly
        reshaped.
        """
        raise NotImplementedError()

    def save(self, filepath: typing.Union[Path, str]) -> None:
        """
        Save the image to a file.
        """
        image: ImageData = self.get_image()
        if isinstance(filepath, str):
            filepath = Path(filepath)
        folder = filepath.parent
        if not folder.exists():
            raise FileNotFoundError(
                f"fails to save image to {folder}: " "folder not found"
            )
        cv2.imwrite(str(filepath), image)

    def display(
        self, label: str = "asi zwo camera", resize: typing.Optional[float] = None
    ) -> None:
        """
        Display the image.

        Arguments:
          label: arbitrary string, used as window's title
          resize: optional resize factor
        """
        image: ImageData = self.get_image()
        if resize is not None:
            w = int(image.shape[1] * resize)
            h = int(image.shape[0] * resize)
            dim = (w, h)
            display_image = cv2.resize(image, dim)
            label = label + f" (display resized: {resize})"
        else:
            display_image = image
        cv2.imshow(label, display_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class ImageRaw8(Image):
    """
    Encapsulate the data of a Raw8 image
    """

    def __init__(self, width: int, height: int) -> None:
        super().__init__(ImageType.raw8, width, height)
        self._data: FlattenData = np.ndarray((width * height), dtype=np.uint8)

    def get_data(self) -> FlattenData:
        return self._data

    def get_data_size(self) -> int:
        return self.width * self.height

    def get_image(self) -> ImageData:
        return self._data.reshape((self.height, self.width))


class ImageY8(Image):
    """
    Encapsulate the data of a Y8 image
    """

    def __init__(self, width: int, height: int) -> None:
        super().__init__(ImageType.y8, width, height)
        self._data: FlattenData = np.ndarray((width * height), dtype=np.uint8)

    def get_data(self) -> FlattenData:
        return self._data

    def get_data_size(self) -> int:
        return self.width * self.height

    def get_image(self) -> ImageData:
        return self._data.reshape((self.height, self.width))


class ImageRGB24(Image):
    """
    Encapsulate the data of a RGB24 image
    """

    def __init__(self, width: int, height: int) -> None:
        super().__init__(ImageType.rgb24, width, height)
        self._data: FlattenData = np.ndarray((width * height * 3), dtype=np.uint8)

    def get_data(self) -> FlattenData:
        return self._data

    def get_data_size(self) -> int:
        return self.width * self.height * 3

    def get_image(self) -> ImageData:
        return self._data.reshape((self.height, self.width, 3))


class ImageRaw16(Image):
    """
    Encapsulate the data of a Raw16 image
    """

    def __init__(self, width: int, height: int) -> None:
        super().__init__(ImageType.raw16, width, height)
        self._data: FlattenData = np.ndarray((width * height * 2), dtype=np.uint8)

    def get_data(self) -> FlattenData:
        return self._data

    def get_data_size(self) -> int:
        return self.width * self.height * 2

    def get_image(self) -> ImageData:
        recasted_data = np.frombuffer(self._data.data, dtype=np.uint16)
        return recasted_data.reshape((self.height, self.width))


ImageClass = typing.Union[
    typing.Type[ImageY8],
    typing.Type[ImageRaw8],
    typing.Type[ImageRaw16],
    typing.Type[ImageRGB24],
]


def get_image_class(image_type: ImageType) -> ImageClass:
    """
    Giving an image type, returns the proper class that
    should be used to encapsulate the related data.
    """

    if image_type == ImageType.raw8:
        return ImageRaw8

    if image_type == ImageType.y8:
        return ImageY8

    if image_type == ImageType.raw16:
        return ImageRaw16

    if image_type == ImageType.rgb24:
        return ImageRGB24

    raise NotImplementedError(f"No support class for image type: {image_type}")


def get_image(image_type: ImageType, width: int, height: int) -> Image:
    """
    Providing an image type and an image size (in pixels), returns
    an instance of the suitable subclass of Image.
    """

    c: ImageClass = get_image_class(image_type)
    return c(width, height)
