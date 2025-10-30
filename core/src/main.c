#include "bitplane_encoder.h"
#include "discrete_wavelet_transform.h"
#include "file_io.h"
#include "segment_header.h"
#include "subband.h"
#include "common.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include "magnitude_encoding.h"

#ifndef EMBEDDED
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

    int32_t* test_data = NULL;
    test_data = calloc((width)*(height),sizeof(int32_t));
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

    uint8_t compressed_data[1024*1024*4] = {};
    //file_io_set_output_file(file_out) ;
    file_io_set_compressed_data_addr(compressed_data);

    SegmentHeader* headers = segment_header_init_values();

    //DEFAULT PARAMETERS START
    //Header 1 is mandatory for each segment. 
    //These values can change for each segment.
    headers->header_1.first_segment = 1;
    headers->header_1.last_segment = 1;
    headers->header_1.segment_index = 0;
    headers->header_1.has_header_2 = 1;
    headers->header_1.has_header_3 = 1;
    headers->header_1.has_header_4 = 1;
    headers->header_1.pad_width = 0;

    //Header 2 is optional.
    //It includes limits for encoding.
    //Changing these makes the compression lossless.
    headers->header_2.stage_stop = 3;
    headers->header_2.seg_byte_limit = 0; //Not used in this implementation.
    headers->header_2.dc_stop = 0;
    headers->header_2.use_fill = 0; //Not used in this implementation.
    headers->header_2.bitplane_stop = 0;

    //Header 3 is optional.
    //These values are allowed to change per segment but are usually fixed.
    headers->header_3.segment_size = (width>>3)*(height>>3);
    headers->header_3.optimal_ac_select = 0;
    headers->header_3.optimal_dc_select = 0;

    //Header 4 is optional.
    //These must be fixed for the entire image.
    headers->header_4.dwt_type = 1;
    headers->header_4.extended_pixel_depth = bitdepth > 16 ? 1 : 0;
    headers->header_4.signed_pixels = 0;
    headers->header_4.pixel_bitdepth = bitdepth % 16;
    headers->header_4.image_width = width;
    headers->header_4.transpose_image = 0;
    headers->header_4.code_word_length = 0;
    headers->header_4.custom_weights = 0;
    //DEFAULT PARAMETERS END
    
    discrete_wavelet_transform_2D(test_data, width, height, 3);

    //Coefficients must be scaled due to the use of the integer wavelet transform.
    //(3.9)
    subband_scale(headers, test_data, width, height);

    size_t num_blocks_total = headers->header_3.segment_size;
    size_t num_blocks = min(BLOCKS_PER_SEGMENT, num_blocks_total);
    size_t num_gaggles = num_blocks / BLOCKS_PER_GAGGLE + (num_blocks % BLOCKS_PER_GAGGLE != 0);

    int32_t* differences_buf = calloc(num_blocks_total, sizeof(int32_t));
    int32_t* shifted_buf = calloc(num_blocks_total, sizeof(int32_t));
    magnitude_encoding_set_buffers(differences_buf, shifted_buf);

    int32_t* dc_coefficients = calloc(num_blocks_total, sizeof(int32_t));
    Block* blocks = calloc(num_blocks_total, sizeof(Block));
    BlockString* block_strings = calloc(num_gaggles, sizeof(BlockString));
    //Writes the trasformed data to the output stream.
    bitplane_encoder_encode(test_data, headers, dc_coefficients, blocks, block_strings);

    file_io_close_output_file();
    //free(headers);

    if(!(fp = fopen(file_out, "wb"))) {
        printf("Failed to open %s for witing!\n", file_out);
        exit(EXIT_FAILURE);
    }

    fwrite(file_io_get_compressed_data_ptr(), 1, file_io_num_bytes_written(), fp);
    fclose(fp);
	return 0;
}
#endif
