#pragma once
#include "ASICamera2.h"
#include "controllable_exception.hpp"

namespace zwo_asi
{
class Controllable
{
public:
    std::string name;
    long min_value;
    long max_value;
    long default_value;
    long value;
    bool is_writable;
    bool is_auto;
    bool supports_auto;
    bool error;
    int error_code;
};

}  // namespace zwo_asi
