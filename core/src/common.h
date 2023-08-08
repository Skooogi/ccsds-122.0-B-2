#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

#define AC_COEFFICIENTS_PER_BLOCK 63
#define BLOCKS_PER_GAGGLE 16

typedef struct Block{
    unsigned bitAC  : 5;
    int32_t dc;
    int32_t ac[AC_COEFFICIENTS_PER_BLOCK]; 
} Block;

inline int32_t max(int32_t a, int32_t b) {  return (a > b) ? a : b; }
inline int32_t min(int32_t a, int32_t b) {  return (a < b) ? a : b; }
uint32_t log2_32 (uint32_t value);
uint32_t twos_complement(int32_t value, size_t num_bits);

#ifdef __cplusplus
}
#endif
#endif //COMMON_H
