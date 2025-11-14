// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#include "block_transform.h"

/*
static uint8_t indices[63] = {
    0,21,42,1,2,3,4,22,
    23,24,25,43,44,45,46,5,
    6,7,8,9,10,11,12,13,
    14,15,16,17,18,19,20,26,
    27,28,29,30,31,32,33,34,
    35,36,37,38,39,40,41,47,
    48,49,50,51,52,53,54,55,
    56,57,58,59,60,61,62
};
    */

static uint8_t reverse[63] = {
    0,3,4,5,6,15,16,17,
    18,19,20,21,22,23,24,25,
    26,27,28,29,30,1,7,8,
    9,10,31,32,33,34,35,36,
    37,38,39,40,41,42,43,44,
    45,46,2,11,12,13,14,47,
    48,49,50,51,52,53,54,55,
    56,57,58,59,60,61,62
};

static void family(Block* blocks, size_t block_index, int32_t* data, size_t width, size_t row, size_t column, size_t ac_index);

void block_transform_pack(Block* blocks, int32_t* dc_coefficients, size_t num_blocks, int32_t* data, size_t data_width) {
    //Picks all coefficients for all blocks from the transformed image.
    //These are held in sequential blocks. (Figure 4-1)

    //Height is not explicitly saved because it can be derived.
    size_t block_width = data_width>>3;
    size_t block_height = num_blocks / block_width;

    //Fill blocks with the families making up the DC coefficients.
    for(size_t row = 0; row < block_height; ++row) {
        for(size_t column = 0; column < block_width; ++column) {
            size_t block_index = row*block_width+column;

            //DC coefficients are held separately.
            dc_coefficients[block_index] = data[row*data_width+column];

            //Parents for F0 F1 F2
            blocks[block_index].ac[0] = data[row*data_width + column + block_width];
            family(blocks, block_index, data, data_width, row, column + block_width, 1);
            blocks[block_index].ac[1] = data[(row+block_height)*data_width + column];
            family(blocks, block_index, data, data_width, row+block_height, column, 22);
            blocks[block_index].ac[2] = data[(row+block_height)*data_width + column+block_width];
            family(blocks, block_index, data, data_width, row+block_height, column+block_width, 43);
        }
    }
}

static void family(Block* blocks, size_t block_index, int32_t* data, size_t width, size_t row, size_t column, size_t ac_index) {
    //Map all coefficients in a single family for a single block.
    //(Table 4-1)

    //Children C_i;
    blocks[block_index].ac[reverse[ac_index+0]]  = data[(2*row)   * width + 2*column];
    blocks[block_index].ac[reverse[ac_index+1]]  = data[(2*row)   * width + 2*column+1];
    blocks[block_index].ac[reverse[ac_index+2]]  = data[(2*row+1) * width + 2*column];
    blocks[block_index].ac[reverse[ac_index+3]]  = data[(2*row+1) * width + 2*column+1];

    //Grandchildren H_i0
    blocks[block_index].ac[reverse[ac_index+4]]  = data[(4*row)   * width + 4*column];
    blocks[block_index].ac[reverse[ac_index+5]]  = data[(4*row)   * width + 4*column+1];
    blocks[block_index].ac[reverse[ac_index+6]]  = data[(4*row+1) * width + 4*column];
    blocks[block_index].ac[reverse[ac_index+7]]  = data[(4*row+1) * width + 4*column+1];

    //Grandchildren H_i1
    blocks[block_index].ac[reverse[ac_index+8]]  = data[(4*row)   * width + 4*column+2];
    blocks[block_index].ac[reverse[ac_index+9]]  = data[(4*row)   * width + 4*column+3];
    blocks[block_index].ac[reverse[ac_index+10]] = data[(4*row+1) * width + 4*column+2];
    blocks[block_index].ac[reverse[ac_index+11]] = data[(4*row+1) * width + 4*column+3];

    //Grandchildren H_i2
    blocks[block_index].ac[reverse[ac_index+12]] = data[(4*row+2) * width + 4*column];
    blocks[block_index].ac[reverse[ac_index+13]] = data[(4*row+2) * width + 4*column+1];
    blocks[block_index].ac[reverse[ac_index+14]] = data[(4*row+3) * width + 4*column];
    blocks[block_index].ac[reverse[ac_index+15]] = data[(4*row+3) * width + 4*column+1];

    //Grandchildren H_i3
    blocks[block_index].ac[reverse[ac_index+16]] = data[(4*row+2) * width + 4*column+2];
    blocks[block_index].ac[reverse[ac_index+17]] = data[(4*row+2) * width + 4*column+3];
    blocks[block_index].ac[reverse[ac_index+18]] = data[(4*row+3) * width + 4*column+2];
    blocks[block_index].ac[reverse[ac_index+19]] = data[(4*row+3) * width + 4*column+3];
}

