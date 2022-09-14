#include "zwo_asi/camera_mode.hpp"

namespace zwo_asi
{
ASI_CAMERA_MODE get_native(CameraMode mode)
{
    switch (mode)
    {
        case CameraMode::normal:
            return ASI_MODE_NORMAL;
        case CameraMode::soft_edge:
            return ASI_MODE_TRIG_SOFT_EDGE;
        case CameraMode::rise_edge:
            return ASI_MODE_TRIG_RISE_EDGE;
        case CameraMode::fall_edge:
            return ASI_MODE_TRIG_FALL_EDGE;
        case CameraMode::soft_level:
            return ASI_MODE_TRIG_SOFT_LEVEL;
        case CameraMode::high_level:
            return ASI_MODE_TRIG_HIGH_LEVEL;
        case CameraMode::low_level:
            return ASI_MODE_TRIG_LOW_LEVEL;
    }
    return ASI_MODE_TRIG_LOW_LEVEL;
}
}  // namespace zwo_asi
