#ifndef CCSDS_EMBEDDED_H
#define CCSDS_EMBEDDED_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void ccsds_compress(int32_t* data, size_t width, size_t height, uint8_t bitdepth);

#ifdef __cplusplus
}
#endif
#endif//CCSDS_EMBEDDED_H
