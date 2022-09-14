#pragma once
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#define UDEV_CHECK "cat /sys/module/usbcore/parameters/usbfs_memory_mb"

namespace zwo_asi
{
namespace internal
{
void append_bool(std::ostringstream& s, bool value, int target_size = -1);
int max_size(const std::vector<std::string> values);
void fix_length(std::string& v, int target_size);
void fix_lengths(std::vector<std::string>& values, int target_size);
std::vector<std::string> long_to_str(const std::vector<long>& values);
bool create_udev_file();
std::string run_system_command(std::string command);

}  // namespace internal

}  // namespace zwo_asi
