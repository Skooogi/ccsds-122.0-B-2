
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "fifo_queue.h"

FifoQueue fifo_queue_init(size_t slot_width) {

    FifoQueue fifo = {};
    fifo.slot_width = slot_width;
    for(uint8_t slot = 0; slot < NUM_TAPS; ++slot) {
        fifo.slots[slot] = malloc(slot_width * sizeof(int32_t));
    }

    return fifo;
}

void fifo_queue_push(FifoQueue* fifo, int32_t* data) {

    int32_t* to_be_replaced = fifo->slots[NUM_TAPS-1];
    for(int8_t slot = NUM_TAPS - 1; slot > 0; --slot) {
        fifo->slots[slot] = fifo->slots[slot - 1]; 
    }
    fifo->slots[0] = to_be_replaced;
    memcpy(fifo->slots[0], data, fifo->slot_width * sizeof(int32_t));
}

int32_t* fifo_queue_get_columns(FifoQueue* fifo) {

    int32_t* coefficients = malloc(NUM_TAPS * fifo->slot_width * sizeof(int32_t));
    for(size_t column = 0; column < fifo->slot_width; ++column) {
        for(uint8_t slot = 0; slot < NUM_TAPS; ++slot) {
            coefficients[column*NUM_TAPS+slot] = fifo->slots[slot][column];
        }
    }
    return coefficients;
}

void fifo_queue_destroy(FifoQueue* fifo) {
    for(uint8_t slot = 0; slot < NUM_TAPS; ++slot) {
        free(fifo->slots[slot]);
    }
}
