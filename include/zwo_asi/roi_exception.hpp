#pragma once
#include <exception>
#include <sstream>
#include <string>
#include "zwo_asi/camera_info.hpp"
#include "zwo_asi/image_type.hpp"

namespace zwo_asi
{
class ROIException : public std::exception
{
public:
    ROIException(int value, int modulo, bool width);
    ROIException(int width,
                 int height,
                 int modulo,
                 std::string camera_description);
    ROIException(int bin);
    ROIException(ImageType type);
    const char* what() const throw();

private:
    std::string error_message_;
};

}  // namespace zwo_asi
