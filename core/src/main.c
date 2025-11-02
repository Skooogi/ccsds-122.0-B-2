#include "ccsds.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>

#ifndef EMBEDDED
int main(int argc, char** argv) {

    if(argc < 6) {
        printf("Usage: ccsds.bin input_file output_file width height bits_per_pixel\n");
        return 0;
    }
    char* file_in = argv[1];
    char* file_out = argv[2];
    char* end;
    uint32_t width = (uint32_t) strtol(argv[3], &end, 10);
    uint32_t height = (uint32_t) strtol(argv[4], &end, 10);
    uint8_t bitdepth = (uint8_t) strtol(argv[5], &end, 10);

    FILE* fp = fopen(file_in, "rb");
    if(!fp) {
        printf("Can not open file %s", file_in);
        return 1;
    }

    int32_t* test_data = NULL;
    test_data = calloc((size_t) ((width)*(height)),sizeof(int32_t));
    uint8_t pad_width = 0;
    uint8_t pad_height = 0;

    //Padding image to multiple of 8
    for(size_t row = 0; row < height; ++row) {
        fread(&test_data[row*(width+pad_width)], sizeof(int32_t), width, fp);
        for(size_t column = width; column < width + pad_width; ++column) {
            test_data[row*(width+pad_width)+column] = test_data[row*(width+pad_width)+width-1];
        }
    }

    for(size_t row = height; row < height + pad_height; ++row) {
        memcpy(&test_data[row*(width+pad_width)], &test_data[(height-1)*(width+pad_width)], (width+pad_width)*sizeof(int32_t));
    }
    if(!test_data) {
        printf("Failed to allocate image!\n");
        exit(EXIT_FAILURE);
    }
    fclose(fp);

    uint32_t dest_size = 1024*1024*4;
    uint8_t compressed_data[1024*1024*4] = {};
    uint32_t compressed_size = 0;

    ccsds_image_compress(
        (uint16_t) width, 
        (uint16_t) height, 
        bitdepth, test_data, 
        (uint8_t*) &compressed_data, 
        dest_size, &compressed_size);

    if(!(fp = fopen(file_out, "wb"))) {
        printf("Failed to open %s for witing!\n", file_out);
        exit(EXIT_FAILURE);
    }

    fwrite(compressed_data, 1, compressed_size, fp);
    fclose(fp);
	return 0;
}
#endif
