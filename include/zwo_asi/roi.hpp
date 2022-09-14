#pragma once
#include "zwo_asi/image_type.hpp"
#include "zwo_asi/roi_exception.hpp"

namespace zwo_asi
{
class ROI
{
public:
    ROI();

public:
    int start_x;
    int start_y;
    int width;
    int height;
    int bins;
    ImageType type;

public:
    void valid(const CameraInfo& info) const;
};

}  // namespace zwo_asi
