#include "discrete_wavelet_transform.h"
#include <stdio.h>

//#define STB_IMAGE_IMPLEMENTATION
//#include "stb_image.h"
//#define STB_IMAGE_WRITE_IMPLEMENTATION
//#include "stb_image_write.h"

extern int32_t test_data;

int main(int argc, char** argv) {

    int32_t side_length = 4096;
	discrete_wavelet_transform_2D(&test_data, side_length, side_length, 3, 0);

	return 0;
}
