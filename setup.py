import inspect
import os
import sys
from pathlib import Path
import cmake_build_extension
import setuptools

init_py = inspect.cleandoc(
    """
    import cmake_build_extension

    with cmake_build_extension.build_extension_env():
        from .bindings import *

    from .camera import Camera
    from .roi import ROI
    from .image import Image
    from .image import ImageType
    from .version import __version__
    """
)

CIBW_CMAKE_OPTIONS = []  # type: ignore
if os.environ.get("CIBUILDWHEEL") == "1":
    if sys.platform == "linux":
        CIBW_CMAKE_OPTIONS += ["-DCMAKE_INSTALL_LIBDIR=lib"]

# Read version without distutils (distutils is removed in Python >=3.12)
version_path = Path("camera_zwo_asi") / "version.py"
version_dict = {}
with version_path.open("r", encoding="utf-8") as version_file:
    exec(version_file.read(), version_dict)

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setuptools.setup(
    ext_modules=[
        cmake_build_extension.CMakeExtension(
            name="Pybind11Bindings",
            install_prefix="camera_zwo_asi",
            cmake_depends_on=["pybind11"],
            write_top_level_init=init_py,
            source_dir=str(Path(__file__).parent.absolute()),
            cmake_configure_options=[
                f"-DPython3_ROOT_DIR={Path(sys.prefix)}",
                "-DCALL_FROM_SETUP_PY:BOOL=ON",
                "-DBUILD_SHARED_LIBS:BOOL=OFF",
            ]
            + CIBW_CMAKE_OPTIONS,
        ),
    ],
    version=version_dict["__version__"],
    description="python wrapper for ZWO astronomical cameras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MPI-IS/camera_zwo_asi",
    license="BSD 3-Clause License",
    author="Vincent Berenz",
    author_email="vberenz@tue.mpg.de",
    cmdclass=dict(
        build_ext=cmake_build_extension.BuildExtension,
    ),
)
