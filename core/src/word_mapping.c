#include "common.h"
#include "file_io.h"
#include "word_mapping.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t sym2bit[4] = { 0, 2, 1, 3 };
static uint8_t sym3bit[2][8] = {
    {1, 4, 0, 5, 2, 6, 3, 7}, 
    {-1, 3, 0, 4, 1, 5, 2, 6}
};

static uint8_t sym4bit[2][16] = {
    {10, 1, 3, 6, 2, 5, 9, 12, 0, 8, 7, 13, 4, 14, 11, 15},
    {-1, 1, 3, 6, 2, 5, 9, 11, 0, 8, 7, 12, 4, 13, 10, 14}
};

static uint8_t word2bit[2][4] = {
    {1, 1, 1, 0},
    {0, 1, 2, 3}
};
static uint8_t word_length_bit_2[4] = { 1, 2, 3, 3 };

static uint8_t word3bit[3][8] = {
    {1, 1, 1, 0, 1, 2, 6, 7},
    {2, 3, 2, 3, 2, 3, 0, 1},
    {0, 1, 2, 3, 4, 5, 6, 7}
};
static uint8_t word_length_bit_3[2][8] = { 
    {1, 2, 3, 5, 5, 5, 6, 6},
    {2, 2, 3, 3, 4, 4, 4, 4}
};

static uint8_t word4bit[4][16] = {
    {1, 1, 1, 1, 0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15},
    {2, 3, 2, 3, 2, 3, 0, 1, 2, 3, 4, 5, 12, 13, 14, 15},
    {4, 5, 6, 7, 4, 5, 6, 7, 4, 5, 6, 7, 0, 1, 2, 3},
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
};
static uint8_t word_length_bit_4[3][16] = { 
    {1, 2, 3, 4, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8},
    {2, 2, 3, 3, 4, 4, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7},
    {3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5}
};

static BlockString block_string = {};
static uint32_t string_length_bit_2[2] = {};
static uint32_t string_length_bit_3[3] = {};
static uint32_t string_length_bit_4[4] = {};

void reset_block_string() {
    memset(&block_string, 0, sizeof(BlockString));
    memset(&string_length_bit_2, 0, 2 * sizeof(uint32_t));
    memset(&string_length_bit_3, 0, 3 * sizeof(uint32_t));
    memset(&string_length_bit_4, 0, 4 * sizeof(uint32_t));
}

void write_block_string() {

    if(block_string.index == 0) {
        return;
    }

    //printf("%u\n", block_string.index);

    uint8_t written_code_options = 0;
    uint8_t code_option_bit_2 = string_length_bit_2[0] <= string_length_bit_2[1] ? 0 : 1;
    uint8_t code_option_bit_3 = 0;
    uint8_t code_option_bit_4 = 0;

    for(uint8_t i = 1; i < 4; ++i) {
        if(i < 3 && string_length_bit_3[i] < string_length_bit_3[code_option_bit_3]){
            code_option_bit_3 = i;
        }

        if(string_length_bit_4[i] < string_length_bit_4[code_option_bit_4]){
            code_option_bit_4 = i;
        }
    }

    for(size_t word_index = 0; word_index < block_string.index; ++word_index) {
        MappedWord current = block_string.mapped_words[word_index];
        uint8_t word, length;

        if(current.length == 0 || current.uncoded) {
            file_io_write_bits(current.mapped_symbol, current.length + 1);
            continue;
        }

        switch(current.length) {
            case 1:
                if((written_code_options & 1) != 1) {
                    file_io_write_bits(code_option_bit_2, 1);
                    written_code_options |= 1;
                    //printf("2: %u %u\n", code_option_bit_2, 1);
                }
                word = word2bit[code_option_bit_2][current.mapped_symbol];
                length = code_option_bit_2 == 1 ? 2 : word_length_bit_2[current.mapped_symbol];
                file_io_write_bits(word, length);
                break;
            case 2:
                if((written_code_options & 2) != 2) {
                    if(code_option_bit_3 == 2) {
                        file_io_write_bits(code_option_bit_3+1, 2);
                    }
                    else {
                        file_io_write_bits(code_option_bit_3, 2);
                    }
                    written_code_options |= 2;
                    //printf("3: %u %u\n", code_option_bit_3, 2);
                }
                word = word3bit[code_option_bit_3][current.mapped_symbol];
                length = code_option_bit_3 == 2 ? 3 : word_length_bit_3[code_option_bit_3][current.mapped_symbol];
                file_io_write_bits(word, length);
                break;
            case 3:
                if((written_code_options & 4) != 4) {
                    file_io_write_bits(code_option_bit_4, 2);
                    //printf("4: %u %u\n", code_option_bit_4, 2);
                    written_code_options |= 4;
                }
                word = word4bit[code_option_bit_4][current.mapped_symbol];
                length = code_option_bit_4 == 3 ? 4 : word_length_bit_4[code_option_bit_4][current.mapped_symbol];
                file_io_write_bits(word, length);
                break;
        }
    } 
}

uint32_t get_bitstring_length() {

    uint8_t code_option_bit_2 = string_length_bit_2[0] <= string_length_bit_2[1] ? 0 : 1;
    uint8_t code_option_bit_3 = 0;
    uint8_t code_option_bit_4 = 0;
    uint8_t written_code_options = 0;

    for(uint8_t i = 1; i < 4; ++i) {
        if(i < 3 && string_length_bit_3[i] < string_length_bit_3[code_option_bit_3]){
            code_option_bit_3 = i;
        }

        if(string_length_bit_4[i] < string_length_bit_4[code_option_bit_4]){
            code_option_bit_4 = i;
        }
    }

    uint64_t total_out_bits = 0;

    for(size_t word_index = 0; word_index < block_string.index; ++word_index) {
        MappedWord current = block_string.mapped_words[word_index];
        uint8_t word, length;

        if(current.length == 0 || current.uncoded) {
            total_out_bits += current.length + 1;
            continue;
        }

        switch(current.length) {
            case 1:
                if((written_code_options & 1) != 1) {
                    total_out_bits += 1;
                    written_code_options |= 1;
                }
                length = code_option_bit_2 == 1 ? 2 : word_length_bit_2[current.mapped_symbol];
                total_out_bits += length;
                break;
            case 2:
                if((written_code_options & 2) != 2) {
                    total_out_bits += 2;
                    written_code_options |= 2;
                }
                length = code_option_bit_3 == 2 ? 3 : word_length_bit_3[code_option_bit_3][current.mapped_symbol];
                total_out_bits += length;
                break;
            case 3:
                if((written_code_options & 4) != 4) {
                    total_out_bits += 2;
                    written_code_options |= 4;
                }
                length = code_option_bit_4 == 3 ? 4 : word_length_bit_4[code_option_bit_4][current.mapped_symbol];
                total_out_bits += length;
                break;
        }
    } 

    return total_out_bits;
}

void word_mapping_code(uint8_t word, uint8_t word_length, uint8_t symbol_option, uint8_t uncoded) {
    
    MappedWord* current = &block_string.mapped_words[block_string.index];
    current->length = word_length - 1;
    current->symbol_option = symbol_option;
    current->uncoded = uncoded;
    block_string.index++;

    if(uncoded || word_length == 1) {
        current->mapped_symbol = word;
        return;
    }

    switch(word_length) {
            
        case 2:
            current->mapped_symbol = sym2bit[word];
            string_length_bit_2[0] += word_length_bit_2[current->mapped_symbol];
            string_length_bit_2[1] += word_length;
            break;
        case 3:
            current->mapped_symbol = sym3bit[symbol_option][word];
            if(current->mapped_symbol == -1) {
                printf("SYMBOL ERROR: 000");
                exit(EXIT_FAILURE);
            }
            string_length_bit_3[0] += word_length_bit_3[0][current->mapped_symbol];
            string_length_bit_3[1] += word_length_bit_3[1][current->mapped_symbol];
            string_length_bit_3[2] += word_length;
            break;
        case 4:
            current->mapped_symbol = sym4bit[symbol_option][word];
            if(current->mapped_symbol == -1) {
                printf("SYMBOL ERROR: 0000");
                exit(EXIT_FAILURE);
            }
            string_length_bit_4[0] += word_length_bit_4[0][current->mapped_symbol];
            string_length_bit_4[1] += word_length_bit_4[1][current->mapped_symbol];
            string_length_bit_4[2] += word_length_bit_4[2][current->mapped_symbol];
            string_length_bit_4[3] += word_length;
            break;
    }
}
