#pragma once

#include <exception>
#include <sstream>
#include <string>

namespace zwo_asi
{
class ControllableException : public std::exception
{
public:
    ControllableException(std::string controllable,
                          long value,
                          long min_value,
                          long max_value);
    ControllableException(std::string controllable,
                          bool no_such_control,
                          bool not_writable,
                          bool no_set_auto);
    const char* what() const throw();

private:
    std::string error_message_;
};

}  // namespace zwo_asi
