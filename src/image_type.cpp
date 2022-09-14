#include "zwo_asi/image_type.hpp"

namespace zwo_asi
{
std::string to_string(ImageType type)
{
    switch (type)
    {
        case ImageType::raw8:
            return "raw8";
        case ImageType::rgb24:
            return "rgb24";
        case ImageType::raw16:
            return "raw16";
        case ImageType::y8:
            return "y8";
    }
    return "";
}

ASI_IMG_TYPE get_native(ImageType type)
{
    switch (type)
    {
        case ImageType::raw8:
            return ASI_IMG_RAW8;
        case ImageType::raw16:
            return ASI_IMG_RAW16;
        case ImageType::rgb24:
            return ASI_IMG_RGB24;
        case ImageType::y8:
            return ASI_IMG_Y8;
    }
    return ASI_IMG_Y8;
}
}  // namespace zwo_asi
