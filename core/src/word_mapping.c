#include "common.h"
#include "file_io.h"
#include "word_mapping.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

//All tables used for symbol and code word mapping. (4.5.3.2.)
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

//Current block string to save to and write from.
static BlockString* block_string;
void set_block_string(BlockString* new_block_string) {
    block_string = new_block_string;
}

void write_block_string() {

    if(block_string->index[block_string->stage] == 0) {
        return;
    }

    uint8_t code_option_bit_2 = block_string->string_length_2_bit[0] <= block_string->string_length_2_bit[1] ? 0 : 1;
    uint8_t code_option_bit_3 = 0;
    uint8_t code_option_bit_4 = 0;

    //Choose the code option for each word length 2...4 that minimizes encoded length.
    for(uint8_t i = 1; i < 4; ++i) {
        if(i < 3 && block_string->string_length_3_bit[i] < block_string->string_length_3_bit[code_option_bit_3]){
            code_option_bit_3 = i;
        }

        if(block_string->string_length_4_bit[i] < block_string->string_length_4_bit[code_option_bit_4]){
            code_option_bit_4 = i;
        }
    }

    //Map and write each word.
    //Before the first occurence of each word length the code word used is written to stream.
    for(size_t word_index = 0; word_index < block_string->index[block_string->stage]; ++word_index) {
        MappedWord current = block_string->mapped_words[block_string->stage][word_index];
        uint8_t word, length;

        if(current.length == 0 || current.uncoded) {
            file_io_write_bits(current.mapped_symbol, current.length+1);
            continue;
        }

        switch(current.length) {
            case 1:
                if((block_string->written_code_options & 1) != 1) {
                    file_io_write_bits(code_option_bit_2, 1);
                    block_string->written_code_options |= 1;
                }
                word = word2bit[code_option_bit_2][current.mapped_symbol];
                length = code_option_bit_2 == 1 ? 2 : word_length_bit_2[current.mapped_symbol];
                file_io_write_bits(word, length);
                break;

            case 2:
                if((block_string->written_code_options & 2) != 2) {

                    //Code options for 3b word are indexed 0,1,3;
                    if(code_option_bit_3 == 2) {
                        file_io_write_bits(code_option_bit_3+1, 2);
                    }
                    else {
                        file_io_write_bits(code_option_bit_3, 2);
                    }
                    block_string->written_code_options |= 2;
                }
                word = word3bit[code_option_bit_3][current.mapped_symbol];
                length = code_option_bit_3 == 2 ? 3 : word_length_bit_3[code_option_bit_3][current.mapped_symbol];
                file_io_write_bits(word, length);
                break;

            case 3:
                if((block_string->written_code_options & 4) != 4) {
                    file_io_write_bits(code_option_bit_4, 2);
                    block_string->written_code_options |= 4;
                }
                word = word4bit[code_option_bit_4][current.mapped_symbol];
                length = code_option_bit_4 == 3 ? 4 : word_length_bit_4[code_option_bit_4][current.mapped_symbol];
                file_io_write_bits(word, length);
                break;
        }
    } 
}

void word_mapping_code(uint8_t word, uint8_t word_length, uint8_t symbol_option, uint8_t uncoded) {
    //Maps each generated word according to 4.5.3.2.
    //The mapped words are held in a BlockString by stage until they are written.
    
    size_t index = block_string->index[block_string->stage];
    MappedWord* current = &block_string->mapped_words[block_string->stage][index];
    current->length = word_length - 1;
    current->symbol_option = symbol_option;
    current->uncoded = uncoded;
    block_string->index[block_string->stage]++;

    //No encoding is necessary and the word is written as is.
    if(uncoded || (word_length == 1)) {
        current->mapped_symbol = word;
        return;
    }

    //The length generated with each code option is saved.
    //This is used to select the code option that minimizes length.
    switch(current->length) {
            
        case 1:
            current->mapped_symbol = sym2bit[word];
            block_string->string_length_2_bit[0] += word_length_bit_2[current->mapped_symbol];
            block_string->string_length_2_bit[1] += word_length;
            break;

        case 2:
            current->mapped_symbol = sym3bit[symbol_option][word];

            //Impossible value.
            if(word == 0 && symbol_option == 1) {
                printf("SYMBOL ERROR: 000\n");
                exit(EXIT_FAILURE);
            }
            block_string->string_length_3_bit[0] += word_length_bit_3[0][current->mapped_symbol];
            block_string->string_length_3_bit[1] += word_length_bit_3[1][current->mapped_symbol];
            block_string->string_length_3_bit[2] += word_length;
            break;

        case 3:
            current->mapped_symbol = sym4bit[symbol_option][word];
            
            //Impossible value.
            if(word == 0 && symbol_option == 1) {
                printf("SYMBOL ERROR: 0000\n");
                exit(EXIT_FAILURE);
            }
            block_string->string_length_4_bit[0] += word_length_bit_4[0][current->mapped_symbol];
            block_string->string_length_4_bit[1] += word_length_bit_4[1][current->mapped_symbol];
            block_string->string_length_4_bit[2] += word_length_bit_4[2][current->mapped_symbol];
            block_string->string_length_4_bit[3] += word_length;
            break;
    }
}
