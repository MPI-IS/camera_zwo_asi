#include "zwo_asi/camera_exception.hpp"

namespace zwo_asi
{
CameraException::CameraException(std::string error_message,
                                 int camera_index,
                                 ASI_ERROR_CODE error_code,
                                 bool udev)
{
    if (udev)
    {
        bool udev_created = internal::create_udev_file();
        std::ostringstream u;
        u << "ASI Camera:\n"
          << "the command '" << UDEV_CHECK
          << "' did not return the expected value of '200' "
          << "which may indicate incorrect udev rules for the ASI camera.\n";
        if (udev_created)
        {
            u << "A file '99-asi.rules' has been created in the current "
                 "directory, please run in a terminal:\n"
              << "  sudo install 99-asi.rules /lib/udev/rules.d\n"
              << "and reconnect the camera\n";
        }
        else
        {
            u << "There has been a failed attempt to create a '99-asi.rules "
                 "file in the current directory.'\n"
              << "See 'install udev rule' in:\n"
              << "https://astronomy-imaging-camera.com/manuals/"
                 "ASI%20Cameras%20software%20Manual%20Linux%20OSX%20EN.pdf";
        }
        error_message_ = u.str();
        return;
    }

    std::ostringstream s;
    s << "ASI Camera: "
      << "(camera index: " << camera_index << ") " << error_message_ << " "
      << "(error code: " << error_code << ": ";
    switch (error_code)
    {
        case ASI_ERROR_INVALID_INDEX:
            s << "ASI_ERROR_INVALID_INDEX"
              << ")";
            break;
        case ASI_ERROR_INVALID_ID:
            s << "ASI_ERROR_ID"
              << ")";
            break;
        case ASI_ERROR_INVALID_CONTROL_TYPE:
            s << "ASI_ERROR_INVALID_CONTROL_TYPE"
              << ")";
            break;
        case ASI_ERROR_CAMERA_CLOSED:
            s << "ASI_ERROR_CAMERA_CLOSED"
              << ")";
            break;
        case ASI_ERROR_CAMERA_REMOVED:
            s << "ASI_ERROR_CAMERA_REMOVED"
              << ")";
            break;
        case ASI_ERROR_INVALID_PATH:
            s << "ASI_ERROR_INVALID_PATH"
              << ")";
            break;
        case ASI_ERROR_INVALID_FILEFORMAT:
            s << "ASI_ERROR_INVALID_FILEFORMAT"
              << ")";
            break;
        case ASI_ERROR_INVALID_SIZE:
            s << "ASI_ERROR_INVALID_SIZE"
              << ")";
            break;
        case ASI_ERROR_INVALID_IMGTYPE:
            s << "ASI_ERROR_INVALID_IMGTYPE"
              << ")";
            break;
        case ASI_ERROR_OUTOF_BOUNDARY:
            s << "ASI_ERROR_OUTOF_BOUNDARY"
              << ")";
            break;
        case ASI_ERROR_TIMEOUT:
            s << "ASI_ERROR_TIMEOUT"
              << ")";
            break;
        case ASI_ERROR_INVALID_SEQUENCE:
            s << "ASI_ERROR_INVALID_SEQUENCE"
              << ")";
            break;
        case ASI_ERROR_BUFFER_TOO_SMALL:
            s << "ASI_ERROR_BUFFER_TOO_SMALL"
              << ")";
            break;
        case ASI_ERROR_VIDEO_MODE_ACTIVE:
            s << "ASI_ERROR_VIDEO_MODE_ACTIVE"
              << ")";
            break;
        case ASI_ERROR_EXPOSURE_IN_PROGRESS:
            s << "ASI_ERROR_EXPOSURE_IN_PROGRESS"
              << ")";
            break;
        case ASI_ERROR_GENERAL_ERROR:
            s << "ASI_ERROR_GENERAL_ERROR"
              << ")";
            break;
    }
    error_message_ = s.str();
}

const char* CameraException::what() const throw()
{
    return error_message_.c_str();
}

}  // namespace zwo_asi
