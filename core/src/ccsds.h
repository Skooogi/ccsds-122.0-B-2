#ifndef CCSDS_H
#define CCSDS_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

void ccsds_image_compress(
    uint16_t height, 
    uint16_t width, 
    uint8_t bitdepth,
    int32_t* pixels,
    uint8_t* dest,
    uint32_t dest_length,
    uint32_t* compressed_size
);

#ifdef __cplusplus
}
#endif
#endif//CCSDS_H
