// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#include "file_io.h"
//#include "FreeRTOS.h"
#include "asw_types.h"
#include <stdio.h>
//#include "asw_assert.h"
//#include "image_data.h"


/// Buffer holding the compressed image data.
static uint8_t *Compressed_Data_Array;

/// The number of bytes that has been written to Compressed_Data_Array.
static size_t Num_Written_Bytes = 0;

static uint32_t bits_written = 0;

static uint8_t cache = 0;
static uint8_t size = 0;


void file_io_set_compressed_data_addr(uint8_t *Address)
{
    Compressed_Data_Array = Address;
}


void file_io_clear(void)
{
    // Clear the array (strictly speaking not needed, but this
    // makes it easier to understand any issues).
    for (size_t I = 0; I < Num_Written_Bytes; I++)
    {
        Compressed_Data_Array[I] = 0;
    }

    // Clear all variables, to allow starting from scratch.
    Num_Written_Bytes = 0;
    bits_written = 0;
    cache = 0;
    size = 0;
}

size_t file_io_num_bytes_written(void)
{
    return Num_Written_Bytes;
}

uint8_t *file_io_get_compressed_data_ptr(void)
{
    return &(Compressed_Data_Array[0]);
}


uint32_t get_bits_written(void) { return bits_written; }

void file_io_write_bits(uint64_t bits, size_t length) {
    //Writes output one byte at a time.

    if (length == 0)
    {
        return;
    }

    bits_written += length;

    for(int32_t i = ((int32_t) length) - 1; i > -1; --i) {
        cache = (uint8_t) (cache << 1);
        cache |= (bits >> (i)) & 1;
        size++;

        if(size >= 8) {

            // Check for out of memory of temporary buffer
            if(Num_Written_Bytes >= MAX_COMPRESSED_DATA_SIZE) {
                printf("FILE IO WROTE TOO MANY BYTES!\n");
            }
            //Assert(Num_Written_Bytes < MAX_COMPRESSED_DATA_SIZE);

            // Write the octet
            Compressed_Data_Array[Num_Written_Bytes] = cache;
            Num_Written_Bytes++;

            cache = 0;
            size = 0;
        }
    }
}

void file_io_close_output_file(void) {
    file_io_write_bits(0, 7);
}
