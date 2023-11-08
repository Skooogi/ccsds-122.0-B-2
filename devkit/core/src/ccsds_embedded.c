#include "ccsds_embedded.h"
#include "segment_header.h"
#include "discrete_wavelet_transform.h"
#include "driver_init.h"
#include "subband.h"
#include "bitplane_encoder.h"
#include "file_io.h"
#include <stdlib.h>
#include <string.h>

typedef struct Packet {
    uint8_t length;
    uint8_t data[64];
    uint8_t crc;
} Packet;

Packet packet;
extern uint8_t send_packet(Packet* packet);
extern uint8_t crc8(uint8_t* data, uint8_t length);

static uint8_t num_words = 0;
void put_word(uint8_t word) {

    packet.data[num_words] = word;
    num_words++;

    if(num_words == 64) {
        packet.crc = crc8((uint8_t*)&packet.data, 64);
        packet.length = 64;
        send_packet(&packet);
        num_words = 0;
        memset(&packet.data, 0, sizeof(packet.data));
    }
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

    file_io_close_output_file();

    free(headers);

    packet.crc = crc8((uint8_t*)&packet.data, num_words);
    packet.length = num_words;
    send_packet(&packet);

}

int32_t min(int32_t a, int32_t b) {
    return (a <= b) * a + (a > b) * b;
}

int32_t max(int32_t a, int32_t b) {
    return (a >= b) * a + (a < b) * b;
}

void _read(void) {}
void _write(void) {}
void _open(void) {}
