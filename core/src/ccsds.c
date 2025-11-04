// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#include "ccsds.h"
#include "bitplane_encoder.h"
#include "discrete_wavelet_transform.h"
#include "file_io.h"
#include "segment_header.h"
#include "subband.h"
#include "common.h"
#include "magnitude_encoding.h"


// The total number of blocks, in the worst case (largest allowed image)
#define MAX_NUM_BLOCKS_TOTAL ((MAX_WIDTH >> 3) * (MAX_HEIGHT >> 3))


// The maximum number of gaggles. This derives from the fact that
// BLOCKS_PER_SEGMENT = 32 and BLOCKS_PER_GAGGLE = 16. If those are
// modified then this would also need modification.
#define MAX_NUM_GAGGLES  (MAX_NUM_BLOCKS_TOTAL/16)


// Temporary data used for magnitude encoding
ALLOCATE_IN_DTCM_64_ALIGNED
static int32_t differences_buf[BLOCKS_PER_SEGMENT];


// Temporary data used for magnitude encoding
ALLOCATE_IN_DTCM_64_ALIGNED
static int32_t shifted_buf[BLOCKS_PER_SEGMENT];


// Temporary data used by the bitplane encoder
ALLOCATE_IN_DTCM_64_ALIGNED
static int32_t dc_coefficients[MAX_NUM_BLOCKS_TOTAL];


// Temporary data used by the bitplane encoder
ALLOCATE_IN_DTCM_64_ALIGNED
static Block blocks[MAX_NUM_BLOCKS_TOTAL];


// Temporary data used by the bitplane encoder
ALLOCATE_IN_DTCM_64_ALIGNED
static BlockString block_strings[MAX_NUM_GAGGLES];


// Implementation of the compression algorithm.
void ccsds_image_compress(
    uint16_t height,
    uint16_t width,
    uint8_t bitdepth,
    int32_t* pixels,
    uint8_t* dest,
    uint32_t dest_length,
    uint32_t* compressed_size) {

    // Start from scratch.
    file_io_clear();

    file_io_set_compressed_data_addr(dest, dest_length);
    SegmentHeader* headers = segment_header_init_values();

    // Header 1.
    headers->header_1.first_segment = 1;
    headers->header_1.last_segment = 1;
    headers->header_1.segment_index = 0;
    headers->header_1.has_header_2 = 1;
    headers->header_1.has_header_3 = 1;
    headers->header_1.has_header_4 = 1;
    headers->header_1.pad_width = 0;

    // Header 2.
    headers->header_2.stage_stop = 3;
    headers->header_2.seg_byte_limit = 0;    // Not used in this implementation.
    headers->header_2.dc_stop = 0;
    headers->header_2.use_fill = 0;          // Not used in this implementation.
    headers->header_2.bitplane_stop = 0;

    // Header 3.
    headers->header_3.segment_size = (((uint32_t) ((width>>3U)*(height>>3U))) & 0x000FFFFFUL);
    headers->header_3.optimal_ac_select = 0;
    headers->header_3.optimal_dc_select = 0;

    //Header 4.
    headers->header_4.dwt_type = 1;
    headers->header_4.extended_pixel_depth = 0;
    headers->header_4.signed_pixels = 0;
    headers->header_4.pixel_bitdepth = (uint16_t) (bitdepth & 0x000FU);
    headers->header_4.image_width = (uint32_t) (width & 0x000FFFFFUL);
    headers->header_4.transpose_image = 0;
    headers->header_4.code_word_length = 0;
    headers->header_4.custom_weights = 0;

    // Perform the wavelet transform on the image.
    discrete_wavelet_transform_2D(pixels, width, height, 3);

    // Coefficients must be scaled due to the use of the integer wavelet
    // transform. (3.9)
    subband_scale(headers, pixels, width, height);

    // Set the temporary buffers used by the magnitude encoding.
    magnitude_encoding_set_buffers(differences_buf, shifted_buf);

    // Writes the trasformed data to the output stream.
    bitplane_encoder_encode(pixels, headers, dc_coefficients, blocks, block_strings);

    // Ensure the cache is flushed.
    file_io_close_output_file();

    // Provide the caller with the information on the amount of bytes written.
    *compressed_size = (uint32_t) file_io_num_bytes_written();
}
