#pragma once
#include "ASICamera2.h"

namespace zwo_asi
{
enum GuideDirection
{
    NORTH,
    SOUTH,
    EAST,
    WEST
};
ASI_GUIDE_DIRECTION get_native(GuideDirection guide);

}  // namespace zwo_asi
