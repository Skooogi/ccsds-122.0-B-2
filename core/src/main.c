#include "bitplane_encoder.h"
#include "discrete_wavelet_transform.h"
#include "file_io.h"
#include "segment_header.h"
#include "subband.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef __SAMV71Q21B__
int main(int argc, char** argv) {

    if(argc < 6) {
        printf("Usage: ccsds.bin input_file output_file width height bits_per_pixel\n");
        return 0;
    }
    char* file_in = argv[1];
    char* file_out = argv[2];
    char* end;
    int32_t width = strtol(argv[3], &end, 10);
    int32_t height = strtol(argv[4], &end, 10);
    uint8_t bitdepth = strtol(argv[5], &end, 10);

    FILE* fp = fopen(file_in, "rb");
    if(!fp) {
        printf("Can not open file %s", file_in);
        return 1;
    }

    uint8_t pad_width = width % 8 ? 8 - width % 8 : 0;
    uint8_t pad_height = height % 8 ? 8 - height % 8 : 0;

    int32_t* test_data = malloc((width+pad_width)*(height+pad_height)*sizeof(int32_t));
    if(!test_data) {
        printf("Failed to allocate image!\n");
        exit(EXIT_FAILURE);
    }

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
    fclose(fp);

    file_io_set_output_file(file_out) ;

    SegmentHeader* headers = segment_header_init_values();
    width += pad_width;
    height += pad_height;
    //TEST PARAMETERS START
    headers->header_1.first_segment = 1;
    headers->header_1.last_segment = 1;
    headers->header_1.num_segments = 1;
    headers->header_1.has_header_3 = 1;
    headers->header_1.has_header_4 = 1;
    headers->header_1.pad_width = pad_width;

    headers->header_3.segment_size = (width>>3)*(height>>3);

    headers->header_4.dwt_type = 1;
    headers->header_4.pixel_bitdepth = bitdepth;
    headers->header_4.image_width = width;
    //TEST PARAMETERS END
    
    discrete_wavelet_transform_2D(test_data, width, height, 3, 0);

    subband_scale(test_data, width, height);

    bitplane_encoder_encode(test_data, headers);

    file_io_close_output_file();
    free(headers);
    free(test_data);
	return 0;
}
#endif
