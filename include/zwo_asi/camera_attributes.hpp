#include <string>
#include "ASICamera2.h"
#include "zwo_asi/bayer_pattern.hpp"

namespace zwo_asi
{
namespace internal
{
class CameraAttributes
{
public:
    CameraAttributes(const ASI_CAMERA_INFO &cam_info);
    std::string to_string() const;

public:
    std::string name;
    long int max_width;
    long int max_height;
    bool colored;
    BayerPattern bayer_pattern;
};

}  // namespace internal

}  // namespace zwo_asi
