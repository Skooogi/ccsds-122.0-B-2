import numpy as np
import math
import matplotlib.pyplot as plt
import bitstream
import code
import rle

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
            blocks[block_i].ac[0] = data[r][2*c]
            family(blocks, block_i, data, r, 2*c, 1)
            blocks[block_i].ac[21] = data[2*r][c]
            family(blocks, block_i, data, 2*r, c, 22)
            blocks[block_i].ac[42] = data[2*r][2*c]
            family(blocks, block_i, data, 2*r, 2*c, 43)

#As in 4-3
def select_coding(delta, J, N):

    if(64*delta > 23*J*pow(2, N)):
        return -1
    elif(207*J > 128*delta):
        return 0
    elif(J*pow(2,N+5) <= 128*delta + 49*J):
        return N-2
    else:
        k = 1
        while(J*pow(2,k+7) <= 128*delta + 49):
            k += 1
        return k


#Width and Height for the LL3 band
def encode(data, width, height, pad_width):

    """
    Divide data as follows
    
    [-----------------------coefficients-----------------------] | WIDTH * HEIGHT DWT transformed pixel values
    [ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ] | b = block = 1 DC and 63 AC coefficients
    [    g   ][    g   ][    g   ][    g   ][    g   ][    g   ] | g = gaggle = 16 blocks
    [              s             ][              s             ] | s = segment = n gaggles, 16 <= n <= 2^20


    """
    blocks = np.empty(int(width/8)*int(height/8), dtype=object)

    for i in range(len(blocks)):
        blocks[i] = code.Block(0,0,0,0,0,0,0,0,0,-2)
        blocks[i].ac = np.zeros(63, dtype = 'int')
        blocks[i].dmax = np.ones(3, dtype='int')*-2
        blocks[i].tran_h = np.zeros(3, dtype='int')


    fill_blocks(blocks, data, int(width/8), int(height/8))

    #Currently partitioned as a single segment
    gaggle_size = 16
    nblocks = blocks.shape[0]
    mod = nblocks % gaggle_size

    #1. Determine AC and DC bitdepths for the segement

    #TODO REMOVE THIS
    #blocks = blocks[-57:-40]

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

    print(bitACGlobal)

    #Determine q (4.3.1.2)
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

    bitstream.fp = open("output.cmp", "wb")

    #Headers part 1 (3 + 1 B) and 4 (8 B)
    header_1  = "1"         #First segment
    header_1 += "1"         #Last segment
    header_1 += "00000001"  #Number of segments
    header_1 += format(bitDC, '05b')
    header_1 += format(bitACGlobal, '05b')
    header_1 += '0'         #reserved
    header_1 += '0'         #Presence of header 2
    header_1 += '1'         #Presence of header 3
    header_1 += '1'         #Presence of header 4

    header_1 += format(pad_width, '03b')
    header_1 += "00000"

    print("header 1", header_1)

    header_3  = format(len(blocks), '020b')
    header_3 += '0' #Heuristic k for DC
    header_3 += '0' #Heuristic k for AC
    header_3 += '00' #reserved

    print("header 3", header_3)

    header_4  = "1" #Integer DWT
    header_4 += "0" #reserved
    header_4 += "0" #pixel depth > 16
    header_4 += "0" #signed
    header_4 += "0000" #pixel depth % 16
    header_4 += format(width, '020b')
    header_4 += "0" #Transpose
    header_4 += "000" #code word
    header_4 += "0" #custom weights
    header_4 += "0"*20 #weights
    header_4 += "0"*11 #reserved

    print("header 4", header_4)

    bitstream.out_bits(header_1+header_3+header_4)

    code.encode_dc_magnitudes(blocks, bitDC, q)
    code.encode_ac_magnitudes(blocks, bitACGlobal, q)
    num = 0
    sym_avg = 0
    total = len(blocks)*(bitACGlobal-1)*4
    for b in range(bitACGlobal-1, -1, -1):

        for stage in range(1):

            for gaggle in range(0, len(blocks), 16):

                bitstring = ""
                bitstream.code.num = np.zeros(4)
                bitstream.code.words = np.array([], dtype='int')
                bitstream.code.sizes = np.array([], dtype='int')
                bitstream.code.symbol_option = np.array([], dtype='int')
                bitstream.code.options = np.array([[0,0],[0,0,0],[0,0,0,0]], dtype=object)

                if(stage == 0):
                    code.stage_0(blocks[gaggle:gaggle+15], q, b)
                elif(stage == 1):
                    code.stage_1(blocks[gaggle:gaggle+15], b)
                elif(stage == 2):
                    code.stage_2(blocks[gaggle:gaggle+15], b)
                elif(stage == 3):
                    code.stage_3(blocks[gaggle:gaggle+15], b)

                bit2 = np.argmin(bitstream.code.options[0])
                bit3 = np.argmin(bitstream.code.options[1])
                bit4 = np.argmin(bitstream.code.options[2]) 

                for idx in range(len(bitstream.code.words)):
                    word = bitstream.code.words[idx]
                    size = bitstream.code.sizes[idx]
                    sym = bitstream.code.symbol_option[idx]

                    if(size == 1):
                        bitstring += str(int(word))
                        continue
                    if(size == 2):
                        bitstring += bitstream.code.word2bit[bit2][bitstream.code.sym2bit[int(word)]]
                        continue
                    if(size == 3):
                        bitstring += bitstream.code.word3bit[bit3][bitstream.code.sym3bit[sym][int(word)]]
                        continue
                    if(size == 4):
                        bitstring += bitstream.code.word4bit[bit4][bitstream.code.sym4bit[sym][int(word)]]
                        continue

                if(sum(bitstream.code.sizes) != 0):
                    #bitstream.out_bits(bitstring)
                    temp = len(bitstring)/sum(bitstream.code.sizes)
                    sym_avg += temp
                    num += 1
                    #if(gaggle/16 % 32 == 0):
                    #    print(b,"Gaggle:", int(gaggle/16),", sym:", temp)
        #code.stage_4(blocks, b)

        progress = len(blocks)*4*(bitACGlobal-1-b)/total*100
        print(f'Encoded {progress:3.1f}%',end='\r')

    print()
    if(num > 0):
        print("AVG:",sym_avg/num)
    bitstream.fp.close()
