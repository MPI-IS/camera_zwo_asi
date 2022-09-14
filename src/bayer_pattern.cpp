#include "zwo_asi/bayer_pattern.hpp"

namespace zwo_asi
{
std::string to_string(BayerPattern bayer)
{
    switch (bayer)
    {
        case BayerPattern::None:
            return "None";
        case BayerPattern::RG:
            return "RG";
        case BayerPattern::BG:
            return "BG";
        case BayerPattern::GR:
            return "GR";
        case BayerPattern::GB:
            return "GB";
    }
    return "";
}
}  // namespace zwo_asi
