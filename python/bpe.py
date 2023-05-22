import numpy as np
import math
import matplotlib.pyplot as plt
import bitstream
import code

def family(blocks, block_i, data, r, c, index):

    #Children C_i
    blocks[block_i][index+1] = data[2*r][2*c]
    blocks[block_i][index+2] = data[2*r][2*c+1]
    blocks[block_i][index+3] = data[2*r+1][2*c]
    blocks[block_i][index+4] = data[2*r+1][2*c+1]

    #Grandchildren H_i0
    blocks[block_i][index+5] = data[4*r][4*c]
    blocks[block_i][index+6] = data[4*r][4*c+1]
    blocks[block_i][index+7] = data[4*r+1][4*c]
    blocks[block_i][index+8] = data[4*r+1][4*c+1]

    #Grandchildren H_i1
    blocks[block_i][index+9] = data[4*r][4*c+2]
    blocks[block_i][index+10] = data[4*r][4*c+3]
    blocks[block_i][index+11] = data[4*r+1][4*c+2]
    blocks[block_i][index+12] = data[4*r+1][4*c+3]

    #Grandchildren H_i2
    blocks[block_i][index+13] = data[4*r+2][4*c]
    blocks[block_i][index+14] = data[4*r+2][4*c+1]
    blocks[block_i][index+15] = data[4*r+3][4*c]
    blocks[block_i][index+16] = data[4*r+3][4*c+1]

    #Grandchildren H_i3
    blocks[block_i][index+17] = data[4*r+2][4*c+2]
    blocks[block_i][index+18] = data[4*r+2][4*c+3]
    blocks[block_i][index+19] = data[4*r+3][4*c+2]
    blocks[block_i][index+20] = data[4*r+3][4*c+3]


def fill_blocks(blocks, data, width, height):

    #Fill blocks with the families making up the DC coefficients
    for r in range(height):
        for c in range(width):
            block_i = r*width+c

            #DC coefficient
            blocks[block_i][0] = data[r][c]

            #Parents for F0 F1 F2
            blocks[block_i][1] = data[r][2*c]
            family(blocks, block_i, data, r, 2*c, 1)

            blocks[block_i][22] = data[2*r][c]
            family(blocks, block_i, data, 2*r, c, 22)

            blocks[block_i][43] = data[2*r][2*c]
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
def encode(data, width, height):

    """
    Divide data as follows
    
    [-----------------------coefficients-----------------------] | WIDTH * HEIGHT DWT transformed pixel values
    [ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ][ b ] | b = block = 1 DC and 63 AC coefficients
    [    g   ][    g   ][    g   ][    g   ][    g   ][    g   ] | g = gaggle = 16 blocks
    [              s             ][              s             ] | s = segment = n gaggles, 16 <= n <= 2^20


    """
    blocks = np.zeros((int(width/8)*int(height/8), 65))
    status = np.zeros((int(width/8)*int(height/8), 63))
    print(blocks.shape)
    fill_blocks(blocks, data, int(width/8), int(height/8))

    #Currently partitioned as a single segment
    gaggle_size = 16
    nblocks = blocks.shape[0]
    mod = nblocks % gaggle_size

    #1. Determine AC and DC bitdepths for the segement

    #Minimum possible values
    bitDC = 1
    bitACGlobal = 0

    for i in range(nblocks):
        #DC value
        dc = blocks[i][0]
        if dc < 0:
            bitDC = max(1 + int(math.log(abs(dc),2)), bitDC)
        else:
            bitDC = max(1 + int(math.log(dc+1,2)), bitDC)

        bitAC = 0
        #Iterate through AC values
        for j in range(1, 64):
            bitAC = max(bitAC, abs(blocks[i][j]))
        bitAC = int(math.log(bitAC + 1,2))
        blocks[i][64] = bitAC
        bitACGlobal = max(bitACGlobal, bitAC)

    #TODO segment header
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

    status = np.zeros((len(blocks),64))
    words = [["" for x in range(16)] for y in range(len(blocks))]

    #Code DC coefficients
    code.encode_dc_magnitudes(blocks[:,0], bitDC, q)
    code.encode_ac_magnitudes(blocks[:,1:], bitACGlobal, q)
    for b in range(bitACGlobal-1, 0, -1):
        code.encode_dc_values(blocks, q, b)
        code.encode_ac_values(status, words, blocks, q, b)
