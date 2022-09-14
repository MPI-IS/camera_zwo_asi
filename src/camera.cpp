#include "zwo_asi/camera.hpp"

namespace zwo_asi
{
std::string get_sdk_version()
{
    return std::string(ASIGetSDKVersion());
}

void close_camera(int camera_index)
{
    ASI_ERROR_CODE error = ASICloseCamera(camera_index);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to close the camera", camera_index, error);
    }
}

Camera::Camera(int camera_index)
    : camera_info_(get_camera_info(camera_index)), camera_index_{camera_index}
{
    ASI_ERROR_CODE error;
    error = ASIOpenCamera(camera_info_.camera_id);
    if (error != ASI_SUCCESS)
    {
        throw CameraException("failed to open the camera", camera_index, error);
    }
    error = ASIInitCamera(camera_info_.camera_id);
    if (error != ASI_SUCCESS)
    {
        throw CameraException("failed to init the camera", camera_index, error);
    }
    read_control_caps(controls_);
}

Camera::~Camera()
{
    ASICloseCamera(camera_info_.camera_id);
}

std::map<std::string, Controllable> Camera::get_controls() const
{
    std::map<std::string, std::shared_ptr<ASI_CONTROL_CAPS>>::const_iterator it;
    std::map<std::string, Controllable> controls;
    for (it = controls_.begin(); it != controls_.end(); it++)
    {
        controls[it->first] = get_controllable(*(it->second));
    }
    return controls;
}

void Camera::set_control(std::string control, long value)
{
    const ASI_CONTROL_CAPS& caps = get_control_caps(control);
    Controllable controllable = get_controllable(caps);
    ASI_ERROR_CODE error =
        ASISetControlValue(camera_index_, caps.ControlType, value, ASI_FALSE);
    if (error != ASI_SUCCESS)
    {
        std::ostringstream s;
        s << "failed to set values for controllable: " << control;
        throw CameraException(s.str(), camera_index_, error);
    }
}

void Camera::set_auto(std::string control)
{
    const ASI_CONTROL_CAPS& caps = get_control_caps(control);
    Controllable controllable = get_controllable(caps);
    if (!controllable.supports_auto)
        throw ControllableException(control, false, false, true);
    ASI_ERROR_CODE error = ASISetControlValue(
        camera_index_, caps.ControlType, controllable.value, ASI_TRUE);
    if (error != ASI_SUCCESS)
    {
        std::ostringstream s;
        s << "failed to set auto-mode for controllable: " << control;
        throw CameraException(s.str(), camera_index_, error);
    }
}

const ASI_CONTROL_CAPS& Camera::get_control_caps(std::string control) const
{
    std::map<std::string, std::shared_ptr<ASI_CONTROL_CAPS>>::const_iterator it;
    it = controls_.find(control);
    if (it == controls_.end())
    {
        throw ControllableException(control, true, false, false);
    }
    return *(it->second);
}

Controllable Camera::get_controllable(const ASI_CONTROL_CAPS& cap) const
{
    Controllable r;
    r.name = std::string(cap.Name);
    ASI_BOOL is_auto_;
    ASI_ERROR_CODE error = ASIGetControlValue(
        camera_index_, cap.ControlType, &(r.value), &is_auto_);
    if (error != ASI_SUCCESS)
    {
        std::ostringstream s;
        s << "failed to read values for parameter " << r.name;
        throw CameraException(s.str(), camera_index_, error);
    }
    if (is_auto_ == ASI_TRUE)
    {
        r.is_auto = true;
    }
    else
    {
        r.is_auto = false;
    }
    r.min_value = cap.MinValue;
    r.max_value = cap.MaxValue;
    r.supports_auto = cap.IsAutoSupported;
    r.is_writable = cap.IsWritable;
    return r;
}

void Camera::configure(ROI roi,
                       std::map<std::string, Controllable> controllables)
{
    set_roi(roi);
    for (auto const& controllable : controllables)
    {
        if (controllable.second.is_writable)
        {
            if (controllable.second.is_auto)
            {
                set_auto(controllable.first);
            }
            else
            {
                set_control(controllable.first, controllable.second.value);
            }
        }
    }
}

ROI Camera::get_roi() const
{
    ROI roi;
    ASI_IMG_TYPE type;
    ASI_ERROR_CODE error = ASIGetROIFormat(
        camera_index_, &roi.width, &roi.height, &roi.bins, &type);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to read the current ROI", camera_index_, error);
    }
    switch (type)
    {
        case ASI_IMG_RAW8:
            roi.type = ImageType::raw8;
            break;
        case ASI_IMG_Y8:
            roi.type = ImageType::y8;
            break;
        case ASI_IMG_RGB24:
            roi.type = ImageType::rgb24;
            break;
        case ASI_IMG_RAW16:
            roi.type = ImageType::raw16;
            break;
    }
    return roi;
}

void Camera::read_control_caps(
    std::map<std::string, std::shared_ptr<ASI_CONTROL_CAPS>>& controls)
{
    int nb_controls;
    ASI_ERROR_CODE error = ASIGetNumOfControls(camera_index_, &nb_controls);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to read the number of controllable parameters",
            camera_index_,
            error);
    }
    for (int control = 0; control < nb_controls; control++)
    {
        std::shared_ptr<ASI_CONTROL_CAPS> caps =
            std::make_shared<ASI_CONTROL_CAPS>();
        error = ASIGetControlCaps(camera_index_, control, caps.get());
        if (error != ASI_SUCCESS)
        {
            std::ostringstream s;
            s << "failed to get parameter value for controllable " << control;
            throw CameraException(s.str(), camera_index_, error);
        }
        controls[std::string{caps->Name}] = caps;
    }
}

ASI_EXPOSURE_STATUS Camera::get_exposition_status() const
{
    ASI_EXPOSURE_STATUS status;
    ASI_ERROR_CODE error = ASIGetExpStatus(camera_index_, &status);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to read the exposure status", camera_index_, error);
    }
    return status;
}

std::string Camera::to_string() const
{
    // reading all current values
    std::map<std::string, Controllable> controls = get_controls();

    // getting names and values of controllable as string
    // of same size, for pretty print
    std::vector<std::string> names;
    std::vector<std::string> values;
    std::vector<std::string> min_values;
    std::vector<std::string> max_values;
    std::vector<Controllable> controllables;
    std::map<std::string, Controllable>::const_iterator it;
    for (it = controls.begin(); it != controls.end(); it++)
    {
        names.push_back(it->first);
        values.push_back(std::to_string(it->second.value));
	min_values.push_back(std::to_string(it->second.min_value));
	max_values.push_back(std::to_string(it->second.max_value));
        controllables.push_back(it->second);
    }
    int names_max = internal::max_size(names);
    internal::fix_lengths(names, names_max + 4);
    int values_max = internal::max_size(values);
    internal::fix_lengths(values, values_max + 2);
    int min_values_max = internal::max_size(min_values);
    internal::fix_lengths(min_values, min_values_max + 2);
    int max_values_max = internal::max_size(max_values);
    internal::fix_lengths(max_values, max_values_max + 2);
    
    // string buffer
    std::ostringstream s;

    // camera infos
    s << std::endl;
    s << "(asi sdk: " << get_sdk_version() << ")" << std::endl;
    s << camera_info_.to_string();
    s << std::endl;

    // adding header for controllables
    std::string controllable("controllable");
    internal::fix_length(controllable, names_max + 4);
    std::string value("value");
    std::string min_value("min value");
    std::string max_value("max value");
    internal::fix_length(value, values_max + 2);
    internal::fix_length(min_value, min_values_max + 5);
    internal::fix_length(max_value, max_values_max + 2);
    s << "|" << controllable << "|" << value
      << " |" << min_value << " |" <<  max_value
      << " |auto-mode  |in auto-mode  |writable\n--\n";

    // adding controllables one by one
    for (int i = 0; i < names.size(); i++)
    {
        const Controllable& control = controllables[i];
        s << "|" << names[i] << "|" << values[i]
	  << " |" << min_values[i] << "    |" << max_values[i]
	  << " ";
        internal::append_bool(s, control.supports_auto, 11);
        internal::append_bool(s, control.is_auto, 14);
        internal::append_bool(s, control.is_writable);
        s << std::endl;
    }

    // returning
    return s.str();
}

void Camera::check_camera_ready() const
{
    ASI_EXPOSURE_STATUS status = get_exposition_status();
    if (status != ASI_EXP_IDLE)
    {
        throw std::runtime_error("could not take a picture: camera busy");
    }
}

ASI_EXPOSURE_STATUS Camera::wait_for_status_change(
    ASI_EXPOSURE_STATUS current_status) const
{
    ASI_EXPOSURE_STATUS status = get_exposition_status();
    while (status == current_status)
    {
        usleep(500);
        status = get_exposition_status();
    }
    return status;
}

void Camera::enable_dark_substract(std::filesystem::path bmp)
{
    if (!std::filesystem::exists(bmp))
    {
        std::ostringstream s;
        s << "file not found: " << bmp;
        throw std::runtime_error(s.str());
    }

    ASI_ERROR_CODE error =
        ASIEnableDarkSubtract(camera_index_, (char*)bmp.string().c_str());
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to enable dark substract", camera_index_, error);
    }
}

void Camera::disable_dark_substract()
{
    ASI_ERROR_CODE error = ASIDisableDarkSubtract(camera_index_);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to disable dark substract", camera_index_, error);
    }
}

void Camera::set_pulse_guide_on(GuideDirection guide)
{
    ASI_ERROR_CODE error =
        ASIPulseGuideOn(camera_index_, zwo_asi::get_native(guide));
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to set pulse guide on", camera_index_, error);
    }
}

void Camera::set_pulse_guide_off(GuideDirection guide)
{
    ASI_ERROR_CODE error =
        ASIPulseGuideOff(camera_index_, zwo_asi::get_native(guide));
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to set off pulse guide", camera_index_, error);
    }
}

void Camera::set_camera_mode(CameraMode mode)
{
    ASI_ERROR_CODE error =
        ASISetCameraMode(camera_index_, zwo_asi::get_native(mode));
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to set camera mode", camera_index_, error);
    }
}

void Camera::set_roi(const ROI& roi)
{
    roi.valid(camera_info_);
    ASI_ERROR_CODE error = ASISetROIFormat(camera_index_,
                                           roi.width,
                                           roi.height,
                                           roi.bins,
                                           zwo_asi::get_native(roi.type));
    if (error != ASI_SUCCESS)
    {
        throw CameraException("failed to set the ROI", camera_index_, error);
    }
    error = ASISetStartPos(camera_index_, roi.start_x, roi.start_y);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to set the ROI starting position", camera_index_, error);
    }
}

const CameraInfo& Camera::get_info() const
{
    return camera_info_;
}

void Camera::capture(unsigned char* buffer, int image_size)
{
    // check that the camera is currently idle, otherwise throws a runtime error
    check_camera_ready();

    // starting exposure. note: exposure time setup by the
    // ASI_EXPOSURE controllable
    ASI_ERROR_CODE error = ASIStartExposure(camera_index_, ASI_FALSE);
    if (error != ASI_SUCCESS)
    {
        throw CameraException("failed to start exposure", camera_index_, error);
    }

    // status is expected to switch status from idle to working to ...
    wait_for_status_change(ASI_EXP_IDLE);
    ASI_EXPOSURE_STATUS new_status = wait_for_status_change(ASI_EXP_WORKING);

    // ... failed !
    if (new_status == ASI_EXP_FAILED)
    {
        throw std::runtime_error("failed to get exposure");
    }

    // ... success ? getting data
    else
    {
        error = ASIGetDataAfterExp(camera_index_, buffer, image_size);
    }

    // did not retrieve the data with success
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to read image after capture", camera_index_, error);
    }
}

}  // namespace zwo_asi
