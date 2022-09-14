#pragma once
#include <string>
#include "ASICamera2.h"

namespace zwo_asi
{
enum ImageType
{
    raw8,
    rgb24,
    raw16,
    y8
};
std::string to_string(ImageType type);
ASI_IMG_TYPE get_native(ImageType type);
}  // namespace zwo_asi
