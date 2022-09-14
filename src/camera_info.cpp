#include "zwo_asi/camera_info.hpp"
#include "zwo_asi/utils.hpp"

namespace zwo_asi
{
static bool get_bool(ASI_BOOL value)
{
    if (value == ASI_TRUE) return true;
    return false;
}

void check_system_udev()
{
    std::string command(UDEV_CHECK);
    std::string usbfs_memory_mb = internal::run_system_command(command);
    usbfs_memory_mb.pop_back();  // last char is return to line
    if (usbfs_memory_mb != std::string("200"))
    {
        throw CameraException("udev error", -1, ASI_ERROR_GENERAL_ERROR, true);
    }
}

int get_nb_cameras()
{
    return ASIGetNumOfConnectedCameras();
}

CameraInfo get_camera_info(int camera_index)
{
    // check_system_udev();

    // no idea why, connecting to the camera may not work if this is not
    // called first
    get_nb_cameras();

    ASI_CAMERA_INFO cam_info;
    CameraInfo info;
    ASI_ERROR_CODE error;
    error = ASIGetCameraProperty(&cam_info, camera_index);
    if (error != ASI_SUCCESS)
    {
        throw CameraException(
            "failed to read camera infos", camera_index, error);
    }

    info.name = std::string(cam_info.Name);
    info.camera_id = cam_info.CameraID;
    info.max_height = cam_info.MaxHeight;
    info.max_width = cam_info.MaxWidth;
    info.is_color = get_bool(cam_info.IsCoolerCam);

    switch (cam_info.BayerPattern)
    {
        case ASI_BAYER_RG:
            info.bayer = BayerPattern::RG;
            break;
        case ASI_BAYER_BG:
            info.bayer = BayerPattern::BG;
            break;
        case ASI_BAYER_GR:
            info.bayer = BayerPattern::GR;
            break;
        case ASI_BAYER_GB:
            info.bayer = BayerPattern::GB;
            break;
    }

    for (int i = 0; i < 16; i++)
    {
        if (cam_info.SupportedBins[i] == 0) break;
        info.supported_bins.insert(cam_info.SupportedBins[i]);
    }

    for (int i = 0; i < 8; i++)
    {
        if (cam_info.SupportedVideoFormat[i] == ASI_IMG_END) break;
        switch (cam_info.SupportedVideoFormat[i])
        {
            case ASI_IMG_RAW8:
                info.supported_image_types.insert(ImageType::raw8);
                break;
            case ASI_IMG_RAW16:
                info.supported_image_types.insert(ImageType::raw16);
                break;
            case ASI_IMG_RGB24:
                info.supported_image_types.insert(ImageType::rgb24);
                break;
            case ASI_IMG_Y8:
                info.supported_image_types.insert(ImageType::y8);
                break;
        }
    }

    info.pixel_size_um = cam_info.PixelSize;
    info.mechanical_shutter = cam_info.MechanicalShutter;
    info.st4_port = get_bool(cam_info.ST4Port);
    info.has_cooler = get_bool(cam_info.IsCoolerCam);
    info.is_usb3_host = get_bool(cam_info.IsUSB3Host);
    info.is_usb3 = get_bool(cam_info.IsUSB3Camera);
    info.elec_per_adu = cam_info.ElecPerADU;
    info.bit_depth = cam_info.BitDepth;
    info.is_trigger = get_bool(cam_info.IsTriggerCam);

    return info;
}

static void add_bool(std::ostringstream& s, std::string label, bool value)
{
    if (value)
    {
        s << label << ": * | ";
    }
    else
    {
        s << label << ": - | ";
    }
}

std::string CameraInfo::to_string() const
{
    std::ostringstream s;
    s << name << " (id: " << camera_id << ")" << std::endl;
    s << "max heigth: (" << max_height << ") | max width: (" << max_width
      << ") |" << std::endl;
    add_bool(s, "colored", is_color);
    add_bool(s, "mechanical shuttger", mechanical_shutter);
    add_bool(s, "st4 port", st4_port);
    s << std::endl;
    add_bool(s, "has cooler", has_cooler);
    add_bool(s, "is usb3 host", is_usb3_host);
    add_bool(s, "is usb3", is_usb3);
    s << std::endl;
    add_bool(s, "is triggered camera", is_trigger);
    s << "bayer pattern: " << zwo_asi::to_string(bayer);
    s << std::endl;
    s << "supported bins: ";
    for (int bin : supported_bins)
    {
        s << bin << " ";
    }
    s << std::endl;
    s << "supported image types: ";
    for (ImageType type : supported_image_types)
    {
        s << zwo_asi::to_string(type) << " ";
    }
    s << std::endl;
    s << "pixel size (um): " << pixel_size_um << " | ";
    s << "elec per ADU: " << elec_per_adu << " | ";
    s << "bit depth: " << bit_depth << std::endl;
    return s.str();
}

}  // namespace zwo_asi
