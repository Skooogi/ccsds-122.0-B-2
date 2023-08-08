#include "common.h"
#include <stdlib.h>

uint32_t log2_32 (uint32_t value) {
    uint32_t result = 0;
    while(value > 1<<result) result++;
    return result;
}

uint32_t twos_complement(int32_t value, size_t num_bits) {
    if(value & 1 << (num_bits - 1)) {
        return (~(abs(value)) + 1) & (1<<(num_bits - 1));
    }
    return value;
}
