#pragma once
#include <set>
#include "ASICamera2.h"
#include "zwo_asi/bayer_pattern.hpp"
#include "zwo_asi/camera_exception.hpp"
#include "zwo_asi/image_type.hpp"

namespace zwo_asi
{
class CameraInfo
{
public:
    std::string name;
    int camera_id;
    long max_height;
    long max_width;
    bool is_color;
    BayerPattern bayer;
    std::set<int> supported_bins;
    std::set<ImageType> supported_image_types;
    double pixel_size_um;
    bool mechanical_shutter;
    bool st4_port;
    bool has_cooler;
    bool is_usb3_host;
    bool is_usb3;
    float elec_per_adu;
    int bit_depth;
    bool is_trigger;

public:
    std::string to_string() const;
};

int get_nb_cameras();
void check_system_udev();
CameraInfo get_camera_info(int camera_index);

}  // namespace zwo_asi
