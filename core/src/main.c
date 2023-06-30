#include "discrete_wavelet_transform.h"

#include <stdio.h>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

int main(int argc, char** argv) {

	//Read image
	char* test_file = "../python/test/test_image_2.bmp";
	int width, height, bpp;
    uint8_t* rgb_image = stbi_load(test_file, &width, &height, &bpp, 1);

	//Copy data for dwt
	int32_t data[width * height];
	for(int i = 0; i < height; ++i) {
		for(int j = 0; j < width; ++j) {
			data[i * width + j] = rgb_image[i * width + j];
		}
	}
	printf("%d %d %d\n", width, height, bpp);
	stbi_image_free(rgb_image);

	int32_t data_cache[width*height];
	memcpy(&data_cache, &data, width*height*sizeof(int32_t));

	int32_t num_iterations = 50;
	for(int i = 0; i < num_iterations; ++i) {
		memcpy(&data, &data_cache, width*height*sizeof(int32_t));
		discrete_wavelet_transform_2D(data, width, height, 3, 0);
	}

	uint8_t* out = malloc(width*height);
	for(int i = 0; i < height; ++i) {
		for(int j = 0; j < width; ++j) {
			out[i * width + j] = data[i * width + j];
		}
	}
	
	printf("Writing file\n");
	stbi_write_png("c_out.bmp", width, height, 1, out, width);
	free(out);
	return 0;
}
