import numpy as np
import math
import run_length_encoding as rle
import word_mapping
import common
import segment_header
import file_io
import discrete_wavelet_transform as dwt
from dataclasses import dataclass
from subband_scaling import rescale

import os, sys
sys.path.append(os.path.abspath('./cython'))
import c_dwt as c_dwt
import struct

decode_trees = []
def readb(num):
    while(len(readb.cache) < num and readb.i < len(readb.data)):
        readb.cache += format(readb.data[readb.i], '08b')
        readb.i += 1

    temp = readb.cache[:num]
    readb.cache = readb.cache[num:]
    return temp

readb.data = 0
readb.cache = ""
readb.i = 0

def decode_header(header):

    header.first_segment  = int(readb(1))
    header.last_segment   = int(readb(1)) 
    header.num_segments   = int(readb(8), 2)
    header.bitDC          = int(readb(5), 2)
    header.bitAC          = int(readb(5), 2)
    readb(1) #reserved
    header.has_header_2   = int(readb(1))  
    header.has_header_3   = int(readb(1))  
    header.has_header_4   = int(readb(1))

    if(header.last_segment == 1):
        header.pad_width      = int(readb(3), 2)
        readb(5) #reserved

    if(header.has_header_2 == 1):
        header.header_2 = segment_header.Header_2()
        header.header_2.seg_byte_limit  = int(readb(27), 2)
        header.header_2.dc_stop         = int(readb(1))
        header.header_2.bitplane_stop   = int(readb(5),2)
        header.header_2.stage_stop      = int(readb(2),2)
        header.header_2.use_fill        = int(readb(1))
        readb(4) #reserved

    if(header.has_header_3 == 1):
        header.header_3 = segment_header.Header_3()
        header.header_3.segment_size    = int(readb(20), 2)
        header.header_3.opt_dc_select   = int(readb(1))
        header.header_3.opt_ac_select   = int(readb(1))
        readb(2) #reserved

    if(header.has_header_4 == 1):
        header.header_4 = segment_header.Header_4()
        header.header_4.dwt_type = int(readb(1))
        readb(1) #reserved
        header.header_4.extended_pixel_depth    = int(readb(1))
        header.header_4.signed_pixels           = int(readb(1))
        header.header_4.pixel_bitdepth          = int(readb(4),2) 
        header.header_4.image_width             = int(readb(20),2) 
        header.header_4.transpose_image         = int(readb(1)) 
        header.header_4.code_word_length        = int(readb(3),2) 
        header.header_4.custom_weights          = int(readb(1)) 
        header.header_4.custom_weight_HH_1      = int(readb(2), 2)
        header.header_4.custom_weight_HL_1      = int(readb(2), 2)
        header.header_4.custom_weight_LH_1      = int(readb(2), 2)
        header.header_4.custom_weight_HH_2      = int(readb(2), 2)
        header.header_4.custom_weight_HL_2      = int(readb(2), 2)
        header.header_4.custom_weight_LH_2      = int(readb(2), 2)
        header.header_4.custom_weight_HH_3      = int(readb(2), 2)
        header.header_4.custom_weight_HL_3      = int(readb(2), 2)
        header.header_4.custom_weight_LH_3      = int(readb(2), 2)
        header.header_4.custom_weight_LL_3      = int(readb(2), 2)
        readb(11) #reserved

    return header

def decode_dc_initial(blocks, bitDC, q):

    #print("Decoding DC magnitudes")
    #DC Magnitudes
    N = max(bitDC - q, 1)

    if(N == 1):
        for i in range(len(blocks)):
            blocks[i].dc = int(readb(1)) << q
        return

    code_word_bits = (math.ceil(math.log(N,2)))
    k = 0

    diffs = np.zeros(len(blocks), dtype='int')
    for i in range(int(len(blocks)/16) + 1):
        k = int(readb(code_word_bits), 2)

        if(i == 0):
            diffs[i] = int(readb(N), 2)

        if(k == 2**code_word_bits-1):
            for j in range(1 if i==0 else 0,16):
                index = i*16+j
                if index >= len(blocks):
                    break
                diffs[index] = int(readb(N), 2)
            continue

        for j in range(1 if i == 0 else 0, 16):
            index = i*16+j
            if(index >= len(blocks)):
               break

            val = 0
            while(b := readb(1)) != '1':
                val += 1
            diffs[index] = val << k

        for j in range(1 if i == 0 else 0, 16):
            index = i*16+j
            if(k == 0 or index >= len(blocks)):
               break
            diffs[index] |= int(readb(k), 2)

    mask = 2**(N-1)-1
    if(diffs[0] & 1 << (N-1)) > 0:
        blocks[0].dc = -(((diffs[0] ^ mask) & mask) + 1)
    else:
        blocks[0].dc = diffs[0]

    for i in range(1, len(blocks)):
        theta = min(blocks[i-1].dc + pow(2, N-1), pow(2, N-1) -1 -blocks[i-1].dc)
        if(diffs[i] > 2*theta):
            if(blocks[i-1].dc < 0):
                diffs[i] = diffs[i] - theta
            else:
                diffs[i] = theta - diffs[i]
        else:
            if(float(diffs[i] / 2) == int(diffs[i] / 2)):
                diffs[i] = diffs[i] / 2
            else:
                diffs[i] = -(diffs[i] + 1) / 2

        blocks[i].dc = (blocks[i-1].dc + diffs[i])

    for i in range(len(blocks)):
        blocks[i].dc = common.twos_complement(blocks[i].dc, N)
        blocks[i].dc <<= q

def decode_ac_magnitudes(blocks, bitACGlobal, q):

    #print("Decoding AC magnitudes")
    #AC Magnitudes
    diffs = np.zeros(len(blocks), dtype='int')
    N = int(abs(math.log(1 + bitACGlobal,2)) + 1)
    if(N == 1):
        for i in range(len(blocks)):
            blocks[i].bitAC = int(readb(1))
        return

    code_word_bits = (math.ceil(math.log(N,2)))
    k = 0

    for i in range(int(len(blocks)/16) + 1):
        k = int(readb(code_word_bits), 2)
        if(i == 0):
            diffs[i] = int(readb(N), 2)

        if(k == 2**code_word_bits-1):
            for j in range(1 if i==0 else 0,16):
                index = i*16+j
                if index >= len(blocks):
                    break
                diffs[index] = int(readb(N), 2)
            continue

        for j in range(1 if i == 0 else 0, 16):
            index = i*16+j
            if(index >= len(blocks)):
               break

            val = 0
            while(b := readb(1)) != '1':
                val += 1
            diffs[index] = val << k

        for j in range(1 if i == 0 else 0, 16):
            index = i*16+j
            if(k == 0 or index >= len(blocks)):
               break
            diffs[index] |= int(readb(k), 2)
    
    blocks[0].bitAC = diffs[0]
    for i in range(1, len(blocks)):
        theta = min(blocks[i-1].bitAC, pow(2, N) -1 - blocks[i-1].bitAC)
        temp = diffs[i]
        if(float(diffs[i] / 2) == int(diffs[i] / 2)):
            diffs[i] = diffs[i] / 2
            if(diffs[i] >= 0 and diffs[i] <= theta):
                blocks[i].bitAC = diffs[i] + blocks[i-1].bitAC
                continue
        else:
            diffs[i] = -(diffs[i] + 1) / 2
            if(diffs[i] <= 0 and diffs[i] >= -theta):
                blocks[i].bitAC = diffs[i] + blocks[i-1].bitAC
                continue

        diffs[i] = temp - theta
        blocks[i].bitAC = diffs[i] + blocks[i-1].bitAC
        if(blocks[i].bitAC < 0 or blocks[i].bitAC > pow(2, N)-1):
            diffs[i] = -diffs[i]
            blocks[i].bitAC = diffs[i] + blocks[i-1].bitAC

def initialize_binary_trees():
    
    global decode_trees
    decode_trees = []
    #Setup binary trees
    word2bit = np.array([["1", "01", "001", "000"], 
                        ["00", "01", "10", "11"]])

    word3bit = np.array([["1", "01", "001", "00000", "00001", "00010", "000110", "000111"], 
                          ["10", "11", "010", "011", "0010", "0011", "0000", "0001"], 
                          ["000", "001", "010", "011", "100", "101", "110", "111"]])

    word4bit = np.array([["1", "01", "001", "0001", "0000000", "0000001", "0000010", "0000011", "00001000", 
                           "00001001", "00001010", "00001011", "00001100", "00001101", "00001110", "00001111"], 
                           ["10", "11", "010", "011", "0010", "0011", "000000", "000001", "000010", 
                            "000011", "000100", "000101", "0001100", "0001101", "0001110", "0001111"], 
                           ["100", "101", "110", "111", "0100", "0101", "0110", "0111", "00100", 
                            "00101", "00110", "00111", "00000", "00001", "00010", "00011"], 
                           ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", 
                            "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"]])


    decode_tree_2 = [rle.NodeTree(),rle.NodeTree()]
    decode_tree_3 = [rle.NodeTree(),rle.NodeTree(),rle.NodeTree()]
    decode_tree_4 = [rle.NodeTree(),rle.NodeTree(),rle.NodeTree(),rle.NodeTree()]
    for i in range(len(word2bit)):
        for j in range(len(word2bit[i])):
            rle.regen_tree(decode_tree_2[i], j, word2bit[i][j])
    for i in range(len(word3bit)):
        for j in range(len(word3bit[i])):
            rle.regen_tree(decode_tree_3[i], j, word3bit[i][j])
    for i in range(len(word4bit)):
        for j in range(len(word4bit[i])):
            rle.regen_tree(decode_tree_4[i], j, word4bit[i][j])
    decode_trees = [decode_tree_2, decode_tree_3, decode_tree_4]


sym2bit = np.array([0, 2, 1, 3])
sym3bit = np.array([[1, 4, 0, 5, 2, 6, 3, 7], [-1, 3, 0, 4, 1, 5, 2, 6]])
sym4bit = np.array([[10, 1, 3, 6, 2, 5, 9, 12, 0, 8, 7, 13, 4, 14, 11, 15], [-1, 1, 3, 6, 2, 5, 9, 11, 0, 8, 7, 12, 4, 13, 10, 14]])

def decode_bits(bitstring, size, symbol_option, code_option):

    if(size == 1):
        return bitstring

    index, skip = rle.read_tree(decode_trees[size-2][code_option], bitstring)
    if(skip == -1):
        return ''

    if(size == 2):
        word = [i for i, x in enumerate(sym2bit) if x == index][0]
        return format(word, '02b')

    if(size == 3):
        if(symbol_option == 1 and index == 7):
            index -= 1
        word = [i for i, x in enumerate(sym3bit[symbol_option]) if x == index][0]
        return format(word, '03b')

    if(size == 4):
        if(symbol_option == 1 and index == 15):
            index -= 1
        word = [i for i, x in enumerate(sym4bit[symbol_option]) if x == index][0]
        return format(word, '04b')

def get_ones(word, bits):
    ones = 0
    for i in range(bits):
        ones += (word >> i) & 1
    return ones

def update_code_words(code_words, length):
    if(length == 1):
        return 0
    index = length - 2 #code_words[0] = 2bit codeword etc

    if(code_words[index] != -1):
        return code_words[index]
    
    code_words[index] = int(readb(1 if length < 3 else 2), 2)
    #print('|'+format(code_words[index], f'0{1 if length == 2 else 2}b')+'|',end='')
    return code_words[index]

def decode_word(num_zeros, symbol_option, code_words, not_tran = True):

    code_word = update_code_words(code_words, num_zeros)

    bitstring = readb(1)
    decoded = decode_bits(bitstring, num_zeros, symbol_option, code_word)
    i = 0
    while decoded == '':
        i += 1
        if(i == 10000):
            raise ValueError("Invalid bitstring: "+bitstring)
        bitstring += readb(1)
        decoded = decode_bits(bitstring, num_zeros, symbol_option, code_word)
    
    decoded_value = int(decoded, 2)
    signs = ''
    if(not_tran and decoded_value):
        signs = readb(get_ones(decoded_value, num_zeros))

    #print(bitstring,end='')
    #if(signs != ''):
    #    print('{'+signs+'}', end='')

    return decoded, signs

def update_tran_word(word, size, decoded):

    for i in range(size):
        if(decoded == ''):
            break
        if(word >> i) & 1:
            continue

        bit = int(decoded[0])
        decoded = decoded[1:]

        word |= bit << i

    if decoded != '':
        raise ValueError(f'decoding lengh mismatch {decoded}')
    return word

def update_ac_values(bitplane, block, offset, span, decoded, signs, families = range(3)):

    for family in families:
        start_index = family*21+offset
        for i in range(span):
            if(decoded == ''):
                break 

            if block.get_status(start_index + i) != 0:
                continue

            bit = int(decoded[0])
            decoded = decoded[1:]

            block.ac[start_index + i] |= bit << bitplane

            sign = 1
            if bit == 1:
                block.set_status(start_index + i, 1)
                sign = int(signs[0])
                signs = signs[1:]

                if(sign == 1):
                    block.ac[start_index + i] |= 1 << block.bitAC

def stage_0(blocks, bitplane, q):
    for i in range(len(blocks)):
        if(3 <= bitplane < q):
            temp = int(readb(1))
            blocks[i].dc |= temp << bitplane
            #print(temp, end='')

    #print()

def stage_1(blocks, bitplane, code_words):

    for i in range(len(blocks)):
        if blocks[i].bitAC < bitplane:
            continue

        new_status_1 = 0
        new_status_2 = 0
        for j in range(63):
            if(common.subband_lim(j, bitplane)):
                new_status_1 |= 1 << j
                new_status_2 |= 1 << j
            elif(blocks[i].get_status(j) > 0):
                new_status_1 |= 1 << j
        blocks[i].set_status_with(new_status_1, new_status_2)

        """
        for j in range(63):
            if(common.subband_lim(j, bitplane)):
                blocks[i].set_status(j, -1)
            elif(blocks[i].get_status(j) == 1 or blocks[i].get_status(j) == 2):
                blocks[i].set_status(j, 2)
            else:
                blocks[i].set_status(j, 0)
        """

        num_zeros  = 1 if blocks[i].get_status(0) == 0 else 0
        num_zeros += 1 if blocks[i].get_status(21) == 0 else 0
        num_zeros += 1 if blocks[i].get_status(42) == 0 else 0
        if(num_zeros == 0):
            continue

        symbol_option = 0
        decoded, signs = decode_word(num_zeros, symbol_option, code_words)

        offset = 0
        span = 1
        update_ac_values(bitplane, blocks[i], offset, span, decoded, signs)
    #print()

def stage_2(blocks, bitplane, code_words):

    for i in range(len(blocks)):
        if blocks[i].bitAC < bitplane:
            continue

        if blocks[i].tran_b == 0:
            blocks[i].tran_b = int(readb(1))
            #print(blocks[i].tran_b,end='')

        if blocks[i].tran_b == 0 or blocks[i].get_bmax() == -1:
            continue

        subband_mask = 0
        subband_mask |= 1 if blocks[i].get_dmax(0) == -1 else 0
        subband_mask |= 2 if blocks[i].get_dmax(1) == -1 else 0
        subband_mask |= 4 if blocks[i].get_dmax(2) == -1 else 0

        blocks[i].tran_d |= subband_mask
        num_zeros = 3 - get_ones(blocks[i].tran_d, 3)
        if num_zeros != 0:

            symbol_option = 1 if num_zeros == 3 else 0
            not_tran = False
            decoded, signs = decode_word(num_zeros, symbol_option, code_words, not_tran)

            size_tran_d = 3
            blocks[i].tran_d = update_tran_word(blocks[i].tran_d, size_tran_d, decoded)
        
        for family in range(3):

            if((blocks[i].tran_d >> family) & 1) != 1:
                continue
            
            first_child_index = 21*family + 1
            num_zeros = 0
            num_zeros  += 1 if blocks[i].get_status(first_child_index+0) == 0 else 0
            num_zeros  += 1 if blocks[i].get_status(first_child_index+1) == 0 else 0
            num_zeros  += 1 if blocks[i].get_status(first_child_index+2) == 0 else 0
            num_zeros  += 1 if blocks[i].get_status(first_child_index+3) == 0 else 0

            if(num_zeros == 0):
                continue

            symbol_option = 0
            decoded, signs = decode_word(num_zeros, symbol_option, code_words)
            offset = 1
            span = 4
            update_ac_values(bitplane, blocks[i], offset, span, decoded, signs, families = [family])
    #print()

def stage_3(blocks, bitplane, code_words):

    for i in range(len(blocks)):
        if blocks[i].bitAC < bitplane:
            continue

        if blocks[i].tran_b == 0:
            continue

        status_f0 = blocks[i].get_gmax(0)
        status_f1 = blocks[i].get_gmax(1)
        status_f2 = blocks[i].get_gmax(2)
        
        subband_mask = 0
        subband_mask |= 4 if status_f2 == -1 else 0
        subband_mask |= 2 if status_f1 == -1 else 0
        subband_mask |= 1 if status_f0 == -1 else 0

        blocks[i].tran_g |= subband_mask
        #TRANG 
        num_zeros =  get_ones(blocks[i].tran_d & (~blocks[i].tran_g & 7), 3)
        if num_zeros != 0:

            symbol_option = 0
            not_tran = False
            decoded, signs = decode_word(num_zeros, symbol_option, code_words, not_tran)

            size_tran_g = 3
            cache_g = blocks[i].tran_g
            blocks[i].tran_g = update_tran_word(blocks[i].tran_g | (~blocks[i].tran_d & 7), size_tran_g, decoded) & blocks[i].tran_d
            blocks[i].tran_g |= cache_g
        #    print(i,'tg', decoded, format(blocks[i].tran_g, '03b'),format(blocks[i].tran_d, '03b'))
        #else:
        #    print(i,'tg', format(blocks[i].tran_g,'03b'), format(blocks[i].tran_d,'03b'))

        #TRANH
        for family in range(3):

            if((blocks[i].tran_g >> family) & 1) == 0:
                continue

            status_hi0 = blocks[i].get_hmax(family, 0)
            status_hi1 = blocks[i].get_hmax(family, 1)
            status_hi2 = blocks[i].get_hmax(family, 2)
            status_hi3 = blocks[i].get_hmax(family, 3)
            
            subband_mask = 0
            subband_mask |= 1 if status_hi0 == -1 else 0
            subband_mask |= 2 if status_hi1 == -1 else 0
            subband_mask |= 4 if status_hi2 == -1 else 0
            subband_mask |= 8 if status_hi3 == -1 else 0
            blocks[i].tran_h[family] |= subband_mask
            num_zeros = 4 - get_ones(blocks[i].tran_h[family], 4)
            if num_zeros == 0:
                continue

            symbol_option = 1 if num_zeros == 4 else 0
            not_tran = False
            decoded, signs = decode_word(num_zeros, symbol_option, code_words, not_tran)
            #if i == 0:
            #    print(num_zeros, family, status_hi0, format(blocks[i].tran_g, '03b'))
            size_tran_h = 4
            blocks[i].tran_h[family] = update_tran_word(blocks[i].tran_h[family], size_tran_h, decoded)

        #types_h and signs_h
        for family in range(3):
            if((blocks[i].tran_g >> family) & 1) == 0:
                continue

            for tran_hj in range(4):
                if((blocks[i].tran_h[family] >> tran_hj) & 1) == 0:
                    continue
            
                first_grandchild_index = 21*family + 5 + 4 * tran_hj

                num_zeros = 0
                num_zeros  += 1 if blocks[i].get_status(first_grandchild_index+0) == 0 else 0
                num_zeros  += 1 if blocks[i].get_status(first_grandchild_index+1) == 0 else 0
                num_zeros  += 1 if blocks[i].get_status(first_grandchild_index+2) == 0 else 0
                num_zeros  += 1 if blocks[i].get_status(first_grandchild_index+3) == 0 else 0

                if(num_zeros == 0):
                    continue

                symbol_option = 1 if num_zeros == 4 else 0
                decoded, signs = decode_word(num_zeros, symbol_option, code_words)
                offset = 5 + 4*tran_hj
                span = 4
                update_ac_values(bitplane, blocks[i], offset, span, decoded, signs, families = [family])
                #if i >= 0:
                    #print(i,family, tran_hj, format(blocks[i].tran_g, '03b'),format(blocks[i].tran_h[family], '04b'), decoded, signs)
            
    #print()

def stage_4(blocks, bitplane):

    for i in range(len(blocks)):
        if(blocks[i].bitAC < bitplane):
            continue

        for pi in range(3):
            index = pi * 21
            if(blocks[i].get_status(index) == 2):
                temp = readb(1)
                #print(temp, end='')
                blocks[i].ac[index] |= int(temp) << bitplane

        for ci in range(3):
            for j in range(4):
                index = 1 + ci*21 + j
                if(blocks[i].get_status(index) == 2):
                    temp = readb(1)
                    #print(temp, end='')
                    blocks[i].ac[index] |= int(temp) << bitplane

        for hi in range(3):
            for hj in range(4):
                for j in range(4):
                    index = 5+hi*21+hj*4+j
                    if(blocks[i].get_status(index) == 2):
                        temp = readb(1)
                        #print(temp, end='')
                        blocks[i].ac[index] |= int(temp) << bitplane
   #print()

def unpack_blocks(blocks, width, height):

    data = np.ones([height*8, width*8], np.int32)

    for row in range(height):
        for column in range(width):
            block_i = row*width+column
            data[row][column] = blocks[block_i].dc
            for family in range(3):
                r = row if family == 0 else row + height
                c = column if family == 1 else column + width
                index = 21 * family

                #P_i
                data[r][c] = blocks[block_i].ac[index]
                index += 1

                #Children C_i
                data[2*r][2*c]     = blocks[block_i].ac[index+0]
                data[2*r][2*c+1]   = blocks[block_i].ac[index+1]
                data[2*r+1][2*c]   = blocks[block_i].ac[index+2]
                data[2*r+1][2*c+1] = blocks[block_i].ac[index+3]

                #Grandchildren H_i0
                data[4*r][4*c]     = blocks[block_i].ac[index+4]
                data[4*r][4*c+1]   = blocks[block_i].ac[index+5]
                data[4*r+1][4*c]   = blocks[block_i].ac[index+6]
                data[4*r+1][4*c+1] = blocks[block_i].ac[index+7]

                #Grandchildren H_i1
                data[4*r][4*c+2]   = blocks[block_i].ac[index+8]
                data[4*r][4*c+3]   = blocks[block_i].ac[index+9]
                data[4*r+1][4*c+2] = blocks[block_i].ac[index+10]
                data[4*r+1][4*c+3] = blocks[block_i].ac[index+11]

                #Grandchildren H_i2
                data[4*r+2][4*c]   = blocks[block_i].ac[index+12]
                data[4*r+2][4*c+1] = blocks[block_i].ac[index+13]
                data[4*r+3][4*c]   = blocks[block_i].ac[index+14]
                data[4*r+3][4*c+1] = blocks[block_i].ac[index+15]

                #Grandchildren H_i3
                data[4*r+2][4*c+2] = blocks[block_i].ac[index+16]
                data[4*r+2][4*c+3] = blocks[block_i].ac[index+17]
                data[4*r+3][4*c+2] = blocks[block_i].ac[index+18]
                data[4*r+3][4*c+3] = blocks[block_i].ac[index+19]

    return data

def decompress():
    #print("Uncompressing file")
    readb.data = 0
    readb.cache = ""
    readb.i = 0

    filename = "output.cmp"

    with open(filename, "rb") as f:
        readb.data = f.read()
    #readb.data = rle.uncompress(readb.data)	

    header = decode_header(segment_header.SegmentHeader)
    bitDC = header.bitDC
    bitACGlobal = header.bitAC
    width = header.header_4.image_width
    pad_width = header.pad_width
    #print(f'[bitDC:{bitDC}, bitACGlobal:{bitACGlobal}, width:{width}, padding:{pad_width}]')
    
    blocks = np.empty(header.header_3.segment_size, dtype=object)
    for i in range(len(blocks)):
        blocks[i] = common.Block()
        blocks[i].dmax = np.ones(3, dtype=int)*-2
        blocks[i].tran_h = np.zeros(3, dtype=int)
        blocks[i].ac = np.zeros(63, dtype=int)
    #print("Blocks:",len(blocks))
    height = int(len(blocks) / int(width/8))*8

    #determine q and N for DC
    q = 0
    if(bitDC <= 3):
        q = 0
    elif(bitDC - int(1 + bitACGlobal/2) <= 1 and bitDC > 3):
        q = bitDC - 3
    elif(bitDC - int(1 + bitACGlobal/2) > 10 and bitDC > 3):
        q = bitDC - 10
    else:
        q = 1 + int(bitACGlobal/2)
    q = max(q, 3)

    decode_dc_initial(blocks, bitDC, q)
    decode_ac_magnitudes(blocks, bitACGlobal, q)

    initialize_binary_trees()

    for bitplane in range(bitACGlobal-1, -1, -1):
        #print("processing bitplane", bitplane)
        for stage in range(4):

            for gaggle in range(0, len(blocks), 16):

                code_words = [-1, -1, -1]
                if(stage == 0):
                    #print("S0")
                    stage_0(blocks[gaggle:gaggle+16], bitplane, q)
                elif(stage == 1):
                    #print("S1")
                    stage_1(blocks[gaggle:gaggle+16], bitplane, code_words)
                elif(stage == 2):
                    #print("S2")
                    stage_2(blocks[gaggle:gaggle+16], bitplane, code_words)
                elif(stage == 3):
                    #print("S3")
                    stage_3(blocks[gaggle:gaggle+16], bitplane, code_words)

        stage_4(blocks, bitplane)
        #print(blocks[0])

    #print("Fixing negatives")
    for i in range(len(blocks)):
        if(blocks[i].dc & (1 << (bitDC - 1))):
            blocks[i].dc = common.twos_complement(blocks[i].dc, bitDC)
            blocks[i].dc *= -1
        
        for j in range(63):
            if blocks[i].ac[j] & (1 << blocks[i].bitAC) > 0:
                blocks[i].ac[j] &= ~(1 << blocks[i].bitAC)
                blocks[i].ac[j] *= -1

    #print("rescaling")
    data = unpack_blocks(blocks, int(width/8), int(height/8))
    rescale(data, width, height)

    #print("IDWT")
    #levels = 3
    #dwt.discrete_wavelet_transform_2D(data, width, height, levels, True)
    #Do DWT in Cython
    num_pixels = width*height
    c_data = np.zeros(num_pixels, dtype='int32')
    for i in range(height):
        for j in range(width):
            c_data[i * width + j] = data[i][j]
    c_data = struct.pack(f'{num_pixels}i', *c_data)

    levels = 3
    c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, True)

    c_data = np.array(struct.unpack(f'{num_pixels}I', c_data)).astype('int32')
    for i in range(height):
        for j in range(width):
            data[i][j] = c_data[i * width + j]
    #end Cython DWT

    file_io.save_image("img_out.bmp", data, width, height) #uncomment if you want to see the result image
    return data

if __name__ == '__main__':
    decompress()
