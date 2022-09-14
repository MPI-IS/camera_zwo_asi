#include "zwo_asi/roi_exception.hpp"

namespace zwo_asi
{
ROIException::ROIException(int value, int modulo, bool width)
{
    std::ostringstream u;
    if (width)
    {
        u << "ROI width%" << modulo << " should be 0 (not the case for "
          << value << ")";
    }
    else
    {
        u << "ROI height%" << modulo << " should be 0 (not the case for "
          << value << ")";
    }
    error_message_ = u.str();
}

ROIException::ROIException(int width,
                           int height,
                           int modulo,
                           std::string camera_description)
{
    std::ostringstream u;
    u << "for camera " << camera_description << ", "
      << "ROI width*height%" << modulo << " should be 0 (not the case for "
      << width << "/" << height << ")";
    error_message_ = u.str();
}

ROIException::ROIException(int bin)
{
    std::ostringstream u;
    u << "unsupported number of bin(s): " << bin;
    error_message_ = u.str();
}

ROIException::ROIException(ImageType type)
{
    std::ostringstream u;
    u << "unsupported image type: " << zwo_asi::to_string(type);
    error_message_ = u.str();
}

const char* ROIException::what() const throw()
{
    return error_message_.c_str();
}

}  // namespace zwo_asi
