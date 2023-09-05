#include "ccsds_embedded.h"
#include "segment_header.h"
#include "discrete_wavelet_transform.h"
#include "subband.h"
#include "bitplane_encoder.h"

int putc(int ch, FILE *f) {
    while(1) {}
}

void ccsds_compress(int32_t* data, size_t width, size_t height, uint8_t bitdepth) {

    SegmentHeader* headers = segment_header_init_values();
    //TEST PARAMETERS START
    headers->header_1.first_segment = 1;
    headers->header_1.last_segment = 1;
    headers->header_1.num_segments = 1;
    headers->header_1.has_header_3 = 1;
    headers->header_1.has_header_4 = 1;
    headers->header_1.pad_width = 0;

    headers->header_3.segment_size = (width>>3)*(height>>3);

    headers->header_4.dwt_type = 1;
    headers->header_4.pixel_bitdepth = bitdepth;
    headers->header_4.image_width = width;
    //TEST PARAMETERS END
    
    discrete_wavelet_transform_2D(data, width, height, 3, 0);

    subband_scale(data, width, height);

    bitplane_encoder_encode(data, headers);
}

int min(int a, int b) {
    return (a < b) * a + (a > b) * b;
}

int max(int a, int b) {
    return (a > b) * a + (a < b) * b;
}

void _read(void) {}
void _write(void) {}
void _open(void) {}
