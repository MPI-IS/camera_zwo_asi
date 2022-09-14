#pragma once
#include <string>
#include "ASICamera2.h"

namespace zwo_asi
{
enum CameraMode
{
    normal,
    soft_edge,
    rise_edge,
    fall_edge,
    soft_level,
    high_level,
    low_level
};
ASI_CAMERA_MODE get_native(CameraMode mode);

}  // namespace zwo_asi
