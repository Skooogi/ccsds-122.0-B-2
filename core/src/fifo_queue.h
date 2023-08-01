#ifndef FIFO_QUEUE_H
#define FIFO_QUEUE_H
#include <stddef.h>
#include <stdint.h>

#define NUM_TAPS 7
typedef struct {
    int32_t* slots[NUM_TAPS];
    size_t slot_width;
} FifoQueue;

FifoQueue fifo_queue_init(size_t slot_width);
void fifo_queue_push(FifoQueue* fifo, int32_t* data);
int32_t* fifo_queue_get_columns(FifoQueue* fifo);
void fifo_queue_destroy(FifoQueue* fifo);

#endif
