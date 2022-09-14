#include "zwo_asi/guide_direction.hpp"

namespace zwo_asi
{
ASI_GUIDE_DIRECTION get_native(GuideDirection guide)
{
    switch (guide)
    {
        case GuideDirection::NORTH:
            return ASI_GUIDE_NORTH;
        case GuideDirection::SOUTH:
            return ASI_GUIDE_SOUTH;
        case GuideDirection::WEST:
            return ASI_GUIDE_WEST;
        case GuideDirection::EAST:
            return ASI_GUIDE_EAST;
    }
    return ASI_GUIDE_EAST;
}

}  // namespace zwo_asi
