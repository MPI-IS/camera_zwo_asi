#pragma once
#include <exception>
#include <string>
#include "ASICamera2.h"
#include "zwo_asi/utils.hpp"

namespace zwo_asi
{
class CameraException : public std::exception
{
public:
    CameraException(std::string error_message,
                    int camera_index,
                    ASI_ERROR_CODE error_code,
                    bool udev = false);
    const char* what() const throw();

private:
    std::string error_message_;
};

}  // namespace zwo_asi
