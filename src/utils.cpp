#include "zwo_asi/utils.hpp"

namespace zwo_asi
{
namespace internal
{
// utils functions used for the Cams.to_string method.

void append_bool(std::ostringstream& s, bool value, int target_size)
{
    if (value)
    {
        s << "|*";
    }
    else
    {
        s << "| ";
    }
    if (target_size > 2)
    {
        for (int j = 0; j < target_size - 1; j++) s << " ";
    }
    return;
}

int max_size(const std::vector<std::string> values)
{
    int max_length = 0;
    for (const std::string& value : values)
    {
        max_length = std::max((int)value.size(), max_length);
    }
    return max_length;
}

void fix_length(std::string& v, int target_size)
{
    if (v.size() >= target_size) return;
    std::ostringstream stream;
    int diff = target_size - v.size();
    for (int j = 0; j < diff; j++) stream << " ";
    v += stream.str();
}

void fix_lengths(std::vector<std::string>& values, int target_size)
{
    std::ostringstream stream;
    for (std::string& v : values)
    {
        fix_length(v, target_size);
    }
}

bool create_udev_file()
{
    std::filesystem::path cwd =
        std::filesystem::current_path() / "99-asi.rules";
    std::ofstream f(cwd.string());
    if (f.is_open())
    {
        f << "ACTION==\"add\", ATTR{idVendor}==\"03c3\", "
          << "RUN+=\"/bin/sh -c '/bin/echo 200 "
             ">/sys/module/usbcore/parameters/usbfs_memory_mb'\"\n"
          << "# All ASI Cameras and filter wheels\n"
          << "SUBSYSTEMS==\"usb\", ATTR{idVendor}==\"03c3\", MODE=\"0666\"\n";
        f.close();
        return true;
    }
    else
    {
        return false;
    }
}

std::string run_system_command(std::string command)
{
    // see:
    // https://www.tutorialspoint.com/How-to-execute-a-command-and-get-the-output-of-command-within-Cplusplus-using-POSIX

    char buffer[128];
    std::string result = "";

    // Open pipe to file
    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe)
    {
        return "popen failed!";
    }

    // read till end of process:
    while (!feof(pipe))
    {
        // use buffer to read and add to result
        if (fgets(buffer, 128, pipe) != NULL) result += buffer;
    }

    pclose(pipe);

    return result;
}

}  // namespace internal

}  // namespace zwo_asi
