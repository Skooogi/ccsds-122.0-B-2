#include "ccsds.h"
#include "bitplane_encoder.h"
#include "discrete_wavelet_transform.h"
#include "file_io.h"
#include "segment_header.h"
#include "subband.h"
#include "common.h"
#include "magnitude_encoding.h"
#include <stdlib.h>

void ccsds_image_compress(
    uint16_t height, 
    uint16_t width, 
    uint8_t bitdepth,
    int32_t* pixels,
    uint8_t* dest,
    uint32_t dest_length,
    uint32_t* compressed_size) {

    file_io_set_compressed_data_addr(dest);
    SegmentHeader* headers = segment_header_init_values();

    #pragma GCC diagnostic push
    #pragma GCC diagnostic ignored "-Warith-conversion"
    #pragma GCC diagnostic ignored "-Wconversion"
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
    headers->header_4.extended_pixel_depth = 0;
    headers->header_4.signed_pixels = 0;
    headers->header_4.pixel_bitdepth = bitdepth;
    headers->header_4.image_width = width;
    headers->header_4.transpose_image = 0;
    headers->header_4.code_word_length = 0;
    headers->header_4.custom_weights = 0;
    //DEFAULT PARAMETERS END
    #pragma GCC diagnostic pop
    
    discrete_wavelet_transform_2D(pixels, width, height, 3);

    //Coefficients must be scaled due to the use of the integer wavelet transform.
    //(3.9)
    subband_scale(headers, pixels, width, height);

    size_t num_blocks_total = headers->header_3.segment_size;
    size_t num_blocks = (size_t) min(BLOCKS_PER_SEGMENT, (int32_t) num_blocks_total);
    size_t num_gaggles = num_blocks / BLOCKS_PER_GAGGLE + (num_blocks % BLOCKS_PER_GAGGLE != 0);

    int32_t* differences_buf = calloc(num_blocks_total, sizeof(int32_t));
    int32_t* shifted_buf = calloc(num_blocks_total, sizeof(int32_t));
    magnitude_encoding_set_buffers(differences_buf, shifted_buf);

    int32_t* dc_coefficients = calloc(num_blocks_total, sizeof(int32_t));
    Block* blocks = calloc(num_blocks_total, sizeof(Block));
    BlockString* block_strings = calloc(num_gaggles, sizeof(BlockString));
    //Writes the trasformed data to the output stream.
    bitplane_encoder_encode(pixels, headers, dc_coefficients, blocks, block_strings);

    file_io_close_output_file();

    *compressed_size = (uint32_t) file_io_num_bytes_written();

    if(dest_length <= *compressed_size) {
        printf("Dest allocation too small!\n");
        exit(EXIT_FAILURE);
    }
}
