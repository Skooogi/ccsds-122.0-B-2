// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef CCSDS_H
#define CCSDS_H
#include <stdint.h>
#include "asw_types.h"
#include <stdio.h>
#include <stdlib.h>
#ifdef __cplusplus
extern "C" {
#endif

#define Assert(x) \
    if (!(x)) { fprintf(stderr,"Assert failed in %s at %s:%d\n!", __func__, __FILE__, __LINE__); abort();}

// Maximum number of columns in an image. Must be a power of 2.
#define MAX_WIDTH    (1024)

// Maximum number of rows in an image. Must be a power of 2.
#define MAX_HEIGHT   (1024)

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
