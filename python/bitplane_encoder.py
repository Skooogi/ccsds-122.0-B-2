import numpy as np
import math
import matplotlib.pyplot as plt

import word_mapping
import file_io
import encode_stages
import run_length_encoding as rle
import common
from segment_header import SegmentHeader

def family(blocks, block_i, data, r, c, index):

    #Children C_i
    blocks[block_i].ac[index+0] = data[2*r][2*c]
    blocks[block_i].ac[index+1] = data[2*r][2*c+1]
    blocks[block_i].ac[index+2] = data[2*r+1][2*c]
    blocks[block_i].ac[index+3] = data[2*r+1][2*c+1]

    #Grandchildren H_i0
    blocks[block_i].ac[index+4] = data[4*r][4*c]
    blocks[block_i].ac[index+5] = data[4*r][4*c+1]
    blocks[block_i].ac[index+6] = data[4*r+1][4*c]
    blocks[block_i].ac[index+7] = data[4*r+1][4*c+1]

    #Grandchildren H_i1
    blocks[block_i].ac[index+8] = data[4*r][4*c+2]
    blocks[block_i].ac[index+9] = data[4*r][4*c+3]
    blocks[block_i].ac[index+10] = data[4*r+1][4*c+2]
    blocks[block_i].ac[index+11] = data[4*r+1][4*c+3]

    #Grandchildren H_i2
    blocks[block_i].ac[index+12] = data[4*r+2][4*c]
    blocks[block_i].ac[index+13] = data[4*r+2][4*c+1]
    blocks[block_i].ac[index+14] = data[4*r+3][4*c]
    blocks[block_i].ac[index+15] = data[4*r+3][4*c+1]

    #Grandchildren H_i3
    blocks[block_i].ac[index+16] = data[4*r+2][4*c+2]
    blocks[block_i].ac[index+17] = data[4*r+2][4*c+3]
    blocks[block_i].ac[index+18] = data[4*r+3][4*c+2]
    blocks[block_i].ac[index+19] = data[4*r+3][4*c+3]


def fill_blocks(blocks, data, width, height):

    #Fill blocks with the families making up the DC coefficients
    for r in range(height):
        for c in range(width):
            block_i = r*width+c

            #DC coefficient
            blocks[block_i].dc = data[r][c]

            #Parents for F0 F1 F2
            blocks[block_i].ac[0] = data[r][c + width]
            family(blocks, block_i, data, r, c + width, 1)
            blocks[block_i].ac[21] = data[r+height][c]
            family(blocks, block_i, data, r+height, c, 22)
            blocks[block_i].ac[42] = data[r+height][c+width]
            family(blocks, block_i, data, r+height, c+width, 43)

def encode(data, width, height, pad_width, bitdepth):

    # [-----------------------coefficients-----------------------] | WIDTH * HEIGHT DWT transformed pixel values
    # [ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ] | b = block = 1 DC and 63 AC coefficients
    # [    g   ][    g   ][    g   ][    g   ][    g   ][    g   ] | g = gaggle = 16 blocks
    # [              s             ][              s             ] | s = segment = n gaggles, 16 <= n <= 2^20
    # 4.1


    #Initialize block array
    blocks = np.empty(int(width/8)*int(height/8), dtype=object)

    for i in range(len(blocks)):
        blocks[i] = common.Block()
        blocks[i].dmax = np.ones(3, dtype=int)*-2
        blocks[i].tran_h = np.zeros(3, dtype=int)
        blocks[i].ac = np.zeros(63, dtype=int)

    fill_blocks(blocks, data, int(width/8), int(height/8))

    #Currently entire image partitioned as a single segment
    #4.1 Determine AC and DC bitdepths for the segement

    #Minimum possible values
    bitDC = 1
    bitACGlobal = 0

    for i in range(len(blocks)):
        #DC value
        dc = int(blocks[i].dc)
        if dc < 0:
            bitDC = max(1 + int(math.log(abs(dc),2)), bitDC)
        else:
            bitDC = max(1 + math.ceil(math.log(dc+1,2)), bitDC)

        bitAC = 0
        #Iterate through AC values
        for j in range(63):
            bitAC = max(bitAC, abs(blocks[i].ac[j]))

        bitAC = math.ceil(math.log(bitAC + 1,2))
        blocks[i].bitAC = bitAC
        bitACGlobal = max(bitACGlobal, bitAC)

    #Determine q (4.3.1.2)
    q_prime = 0
    if(bitDC <= 3):
        q_prime = 0
    elif(bitDC - int(1 + bitACGlobal/2) <= 1 and bitDC > 3):
        q_prime = bitDC - 3
    elif(bitDC - int(1 + bitACGlobal/2) > 10 and bitDC > 3):
        q_prime = bitDC - 10
    else:
        q_prime = 1 + int(bitACGlobal/2)

    q = max(q_prime, 3)

    #TODO: Separate segment header generation
    header = SegmentHeader()
    header.first_segment    = 1
    header.last_segment     = 1
    header.num_segments     = 1
    header.bitDC            = bitDC
    header.bitAC            = bitACGlobal
    header.has_header_3     = 1
    header.has_header_4     = 1
    header.pad_width        = pad_width

    header.header_3.segment_size = len(blocks)
    
    header.header_4.pixel_bitdepth = bitdepth
    header.header_4.image_width = width

    file_io.out_bits(str(header))

    #Encode all coefficients
    encode_stages.encode_dc_initial(blocks, bitDC, q)
    encode_stages.encode_ac_magnitudes(blocks, bitACGlobal, q)

    #process every bitplane and stage gaggle by gaggle
    #Figure 4-2
    for b in range(bitACGlobal-1, -1, -1):

        #print("processing bitplane", b)
        for stage in range(4):

            for gaggle in range(0, len(blocks), 16):

                bitstring = ""
                word_mapping.words = []
                word_mapping.sizes = []
                word_mapping.symbol_option = []
                word_mapping.options = np.array([[0,0],[0,0,0],[0,0,0,0]], dtype=object)

                if(stage == 0):
                    #print("S0")
                    encode_stages.stage_0(blocks[gaggle:gaggle+16], q, b)
                elif(stage == 1):
                    #print("S1")
                    encode_stages.stage_1(blocks[gaggle:gaggle+16], b)
                elif(stage == 2):
                    #print("S2")
                    encode_stages.stage_2(blocks[gaggle:gaggle+16], b)
                elif(stage == 3):
                    #print("S3")
                    encode_stages.stage_3(blocks[gaggle:gaggle+16], b)

                #Choose the coding option that minimizes the bitstring length for this gaggle
                #Each word length has a separate coding option
                #4.5.3.3.5
                #Code word is written if the current word is the first of its length in this gaggle.
                bit2 = np.argmin(word_mapping.options[0])
                bit3 = np.argmin(word_mapping.options[1])
                bit4 = np.argmin(word_mapping.options[2]) 

                written_code_option = 0

                #Each word is mapped using the optimal coding option and written to file
                for idx in range(len(word_mapping.words)):
                    word = word_mapping.words[idx]
                    size = word_mapping.sizes[idx]
                    sym = word_mapping.symbol_option[idx]

                    if(size < 0):
                        #Negative sizes denote uncoded bits for which no word mapping is performed
                        bitstring += '{'+format(word, f'0{size*-1}b')+'}'
                        continue

                    if(size == 1):
                        bitstring += ''+format(word, '01b')+''
                        continue

                    if(size == 2):
                        if(not written_code_option & 1):
                            bitstring += '|'+format(bit2,'01b')+'|'
                            written_code_option |= 1
                        bitstring += word_mapping.word2bit[bit2][word_mapping.sym2bit[int(word)]]
                        continue

                    if(size == 3):
                        if(not written_code_option & 2):
                            bitstring += '|'+format(bit3,'02b')+'|'
                            written_code_option |= 2
                        bitstring += word_mapping.word3bit[bit3][word_mapping.sym3bit[sym][int(word)]]
                        continue

                    if(size == 4):
                        if(not written_code_option & 4):
                            bitstring += '|'+format(bit4,'02b')+'|'
                            written_code_option |= 4
                        bitstring += word_mapping.word4bit[bit4][word_mapping.sym4bit[sym][int(word)]]
                        continue

                if(len(bitstring)):
                    #print(bitstring)
                    file_io.out_bits(bitstring.replace('|','').replace('{','').replace('}','').replace('[','').replace(']',''))

        encode_stages.stage_4(blocks, b)
