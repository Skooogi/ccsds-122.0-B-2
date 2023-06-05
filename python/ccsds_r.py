import numpy as np
import math
import rle
from dataclasses import dataclass

@dataclass
class Block:
    bitAC: int
    dc: int
    status1: np.ulonglong
    status2: np.ulonglong
    tran_p: int
    tran_b: int
    tran_d: int
    tran_g: int
    bmax: int
    dmax: np.ndarray = np.zeros(3, dtype='int')
    tran_h: np.ndarray = np.zeros(3, dtype='int')
    ac: np.ndarray = np.zeros(63)

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

def twos(value, bits):
    if(value & 1 << (bits - 1)):
        return ~value + 1
    
    return value

def stage_0(blocks, b, q):
    for i in range(len(blocks)):
        if(3 <= b < q):
            blocks[i].dc |= int(readb(1)) << b


if __name__ == '__main__':
    print("Uncompressing file")

    filename = "output.cmp"

    #rle.uncompress(filename, filename)

    with open(filename, "rb") as f:
        readb.data = f.read()

    readb(10)
    bitDC = int(readb(5),2)
    bitACGlobal = int(readb(5),2)
    readb(4)
    pad_width = int(readb(3), 2)
    readb(5)
    num_blocks = int(readb(20), 2)
    readb(12)
    width = int(readb(20), 2)
    readb(36)

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

    print(f'[bitDC:{bitDC}, bitACGlobal:{bitACGlobal}, width:{width}, padding:{pad_width}]')

    blocks = np.empty(num_blocks, dtype=object)
    for i in range(len(blocks)):
        blocks[i] = Block(0,0,0,0,0,0,0,0,0,-2)
        blocks[i].ac = np.zeros(63, dtype = 'int')
        blocks[i].dmax = np.ones(3, dtype='int')*-2
        blocks[i].tran_h = np.zeros(3, dtype='int')

    print("Decoding DC magnitudes")
    #DC Magnitudes
    N = max(bitDC - q, 1)
    code_word_bits = (math.ceil(math.log(N,2)))
    k = 0

    diffs = np.zeros(len(blocks), dtype='int')
    for i in range(int(len(blocks)/16) + 1):
        k = int(readb(code_word_bits), 2)
        if(i == 0):
            diffs[i] = int(readb(8), 2)

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
            if(index >= len(blocks)):
               break
            diffs[index] |= int(readb(k), 2)

    if(diffs[0] & 1 << (N-1)) > 0:
        blocks[0].dc = diffs[0]*-1
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

        blocks[i].dc = abs(blocks[i-1].dc + diffs[i])

    for i in range(len(blocks)):
        blocks[i].dc <<= q
        blocks[i].dc = twos(blocks[i].dc, bitDC)

    print("Decoding AC magnitudes")
    #AC Magnitudes
    diffs = np.zeros(len(blocks), dtype='int')
    N = int(abs(math.log(1 + bitACGlobal,2)) + 1)
    code_word_bits = (math.ceil(math.log(N,2)))
    k = 0

    for i in range(int(len(blocks)/16) + 1):
        k = int(readb(code_word_bits), 2)
        if(i == 0):
            diffs[i] = int(readb(8), 2)

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
            if(index >= len(blocks)):
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

    #AC coeffs
    print("Decoding AC coeffs")
    for b in range(bitACGlobal-1, -1, -1):
        for stage in range(1):
            for gaggle in range(0, len(blocks), 16):
                if(stage == 0):
                    stage_0(blocks[gaggle:gaggle+16], b, q)

    for i in range(len(blocks)):
        print(blocks[i].dc)
