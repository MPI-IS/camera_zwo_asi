#include "zwo_asi/controllable_exception.hpp"

namespace zwo_asi
{
ControllableException::ControllableException(std::string controllable,
                                                   long value,
                                                   long min_value,
                                                   long max_value)
{
    std::ostringstream s;
    s << "out of bound value for " << controllable << ": " << value
      << "is not in the range " << min_value << "; " << max_value;
    error_message_ = s.str();
}

ControllableException::ControllableException(std::string controllable,
                                                   bool no_such_control,
                                                   bool not_writable,
                                                   bool no_set_auto)
{
    std::ostringstream s;
    if (no_such_control)
    {
        s << "no such controllable: " << controllable;
    }
    if (not_writable)
    {
        s << "failed to change the value of " << controllable << ": "
          << "not writable";
    }
    if (no_set_auto)
    {
        s << "failed to change the value of " << controllable << ": "
          << "to auto-mode (not supported)";
    }
    error_message_ = s.str();
}

const char* ControllableException::what() const throw()
{
    return error_message_.c_str();
}

}  // namespace zwo_asi
