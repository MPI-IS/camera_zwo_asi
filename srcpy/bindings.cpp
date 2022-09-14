#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "zwo_asi/camera.hpp"

using namespace zwo_asi;

void capture(Camera& camera, pybind11::array_t<unsigned char>& image, int image_size)
{
  pybind11::buffer_info buffer = image.request();
  camera.capture((unsigned char*)buffer.ptr, image_size);
}

PYBIND11_MODULE(bindings, m)
{

  m.doc() = "zwo_asi bindings";

  pybind11::enum_<BayerPattern>(m, "BayerPattern")
    .value("None", None)
    .value("RG", RG)
    .value("BG", BG)
    .value("GR", GR)
    .value("GB", GB);

  pybind11::enum_<ImageType>(m, "ImageType")
    .value("raw8", raw8)
    .value("rgb24", rgb24)
    .value("raw16", raw16)
    .value("y8", y8);

  pybind11::enum_<GuideDirection>(m, "GuideDirection")
    .value("NORTH", NORTH)
    .value("SOUTH", SOUTH)
    .value("EAST", EAST)
    .value("WEST", WEST);

  pybind11::enum_<CameraMode>(m, "CameraMode")
    .value("normal", normal)
    .value("soft_edge", soft_edge)
    .value("rise_edge", rise_edge)
    .value("fall_edge", fall_edge)
    .value("soft_level", soft_level)
    .value("high_level", high_level)
    .value("low_level", low_level);
    
  pybind11::class_<ControllableException>(m, "ControllableException")
    .def(pybind11::init<std::string,long,long,long>())
    .def(pybind11::init<std::string,bool,bool,bool>());

  pybind11::class_<Controllable>(m,"Controllable")
    .def_readonly("name",&Controllable::name)
    .def_readonly("min_value",&Controllable::min_value)
    .def_readonly("max_value",&Controllable::max_value)
    .def_readonly("default_value",&Controllable::default_value)
    .def_readwrite("value",&Controllable::value)
    .def_readonly("is_writable",&Controllable::is_writable)
    .def_readwrite("is_auto",&Controllable::is_auto)
    .def_readonly("supports_auto",&Controllable::supports_auto);

  pybind11::class_<ROI>(m,"ROI")
    .def(pybind11::init<>())
    .def_readwrite("start_x",&ROI::start_x)
    .def_readwrite("start_y",&ROI::start_y)
    .def_readwrite("width",&ROI::width)
    .def_readwrite("height",&ROI::height)
    .def_readwrite("bins",&ROI::bins)
    .def_readwrite("type",&ROI::type)
    .def("valid",&ROI::valid);
  
  pybind11::class_<CameraInfo>(m,"CameraInfo")
    .def_readonly("name",&CameraInfo::name)
    .def_readonly("camera_id",&CameraInfo::camera_id)
    .def_readonly("max_height",&CameraInfo::max_height)
    .def_readonly("max_width",&CameraInfo::max_width)
    .def_readonly("is_color",&CameraInfo::is_color)
    .def_readonly("bayer",&CameraInfo::bayer)
    .def_readonly("supported_bins",&CameraInfo::supported_bins)
    .def_readonly("supported_image_types",&CameraInfo::supported_image_types)
    .def_readonly("pixel_size_um",&CameraInfo::pixel_size_um)
    .def_readonly("mechanical_shutter",&CameraInfo::mechanical_shutter)
    .def_readonly("st4_port",&CameraInfo::st4_port)
    .def_readonly("has_cooler",&CameraInfo::has_cooler)
    .def_readonly("is_usb3_host",&CameraInfo::is_usb3_host)
    .def_readonly("is_usb3",&CameraInfo::is_usb3)
    .def_readonly("elec_per_adu",&CameraInfo::elec_per_adu)
    .def_readonly("bit_depth",&CameraInfo::bit_depth)
    .def_readonly("is_trigger",&CameraInfo::is_trigger);
    
  pybind11::class_<CameraException>(m, "CameraException")
    .def(pybind11::init<std::string,int,ASI_ERROR_CODE,bool>());

  m.def("get_nb_cameras", &get_nb_cameras);
  m.def("get_sdk_version", &get_sdk_version);
  m.def("close_camera", &close_camera);
  m.def("create_udev_file", &internal::create_udev_file);
  
  pybind11::class_<Camera>(m, "Camera")
    .def(pybind11::init<int>())
    .def("set_roi", &Camera::set_roi)
    .def("get_roi", &Camera::get_roi)
    .def("get_controls", &Camera::get_controls)
    .def("set_control", &Camera::set_control)
    .def("set_auto", &Camera::set_auto)
    .def("set_camera_mode", &Camera::set_camera_mode)
    .def("set_pulse_guide_on", &Camera::set_pulse_guide_on)
    .def("set_pulse_guide_off", &Camera::set_pulse_guide_off)
    .def("enable_dark_substract", &Camera::enable_dark_substract)
    .def("disable_dark_substract", &Camera::disable_dark_substract)
    .def("__str__", &Camera::to_string)
    .def("get_info", &Camera::get_info)
    .def("capture", &capture);
}
