#include "zwo_asi/roi.hpp"

namespace zwo_asi
{
ROI::ROI()
    : start_x{0}, start_y{0}, width{0}, height{0}, bins{0}, type{ImageType::y8}
{
}

void ROI::valid(const CameraInfo& info) const
{
    if (width % 8 != 0)
    {
        throw ROIException(width, 8, true);
    }
    if (height % 2 != 0)
    {
        throw ROIException(height, 2, false);
    }
    if (info.name == std::string("ASI120") && !info.is_usb3 &&
        width * height % 1024 != 0)
    {
        throw ROIException(width, height, 1024, "ASI120");
    }
    auto found_bin = info.supported_bins.find(bins);
    if (found_bin == info.supported_bins.end())
    {
        throw ROIException(bins);
    }
    auto found_type = info.supported_image_types.find(type);
    if (found_type == info.supported_image_types.end())
    {
        throw ROIException(type);
    }
}

}  // namespace zwo_asi
