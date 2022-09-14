#pragma once
#include <algorithm>
#include "zwo_asi/camera_exception.hpp"
#include "zwo_asi/camera_info.hpp"
#include "zwo_asi/camera_mode.hpp"
#include "zwo_asi/controllable.hpp"
#include "zwo_asi/guide_direction.hpp"
#include "zwo_asi/camera_attributes.hpp"
#include "zwo_asi/roi.hpp"

namespace zwo_asi
{
std::string get_sdk_version();
void close_camera(int camera_index);

class Camera
{
public:
    Camera(int camera_index);
    ~Camera();
    std::map<std::string, Controllable> get_controls() const;
    ROI get_roi() const;
    void set_control(std::string control, long value);
    void set_auto(std::string control);
    void set_camera_mode(CameraMode mode);
    void set_pulse_guide_on(GuideDirection guide);
    void set_pulse_guide_off(GuideDirection guide);
    void enable_dark_substract(std::filesystem::path bmp);
    void disable_dark_substract();
    std::string to_string() const;
    void capture(unsigned char* buffer, int image_size);
    const CameraInfo& get_info() const;
    void configure(ROI roi, std::map<std::string, Controllable>);
    void set_roi(const ROI& roi);

private:
    const ASI_CONTROL_CAPS& get_control_caps(std::string control) const;
    Controllable get_controllable(const ASI_CONTROL_CAPS& cap) const;
    ASI_EXPOSURE_STATUS get_exposition_status() const;
    void check_camera_ready() const;
    ASI_EXPOSURE_STATUS wait_for_status_change(
        ASI_EXPOSURE_STATUS status) const;
    void read_control_caps(
        std::map<std::string, std::shared_ptr<ASI_CONTROL_CAPS>>& controls);

private:
    CameraInfo camera_info_;
    int camera_index_;
    std::map<std::string, std::shared_ptr<ASI_CONTROL_CAPS>> controls_;
};

}  // namespace zwo_asi
