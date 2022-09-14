#pragma once
#include <string>

namespace zwo_asi
{
enum BayerPattern
{
    None,
    RG,
    BG,
    GR,
    GB
};
std::string to_string(BayerPattern bayer);
}  // namespace zwo_asi
