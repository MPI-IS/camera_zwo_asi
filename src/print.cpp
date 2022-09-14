#include "zwo_asi/camera.hpp"

int main()
{
    try
    {
        int nb_cameras = zwo_asi::get_nb_cameras();

        if (nb_cameras == 0)
        {
            std::cout << "no camera detected" << std::endl;
        }

        for (int cam_index = 0; cam_index < nb_cameras; cam_index++)
        {
            zwo_asi::Camera camera(cam_index);
            std::string s = camera.to_string();
            std::cout << s << std::endl;
        }
    }
    catch (std::exception& e)
    {
        std::cout << "failed: " << e.what() << std::endl;
        EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
