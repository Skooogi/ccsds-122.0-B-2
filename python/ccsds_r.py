import numpy as np
import math
import run_length_encoding as rle
import bitstream
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

def twos(value, bits):
    if(value & 1 << (bits - 1)):
        return ~value + 1
    
    return value

def int_to_status(block, i, temp):
    val = 3 if temp == -1 else temp

    block.status1 |= ((val >> 1) & 1) << i
    block.status2 |= (val & 1) << i
def subband_lim(j, b):

    if(j == 0 or j == 21) and b < 3:
        return True
    elif((1 <= j <= 4) or (22 <= j <= 25) or j == 42) and b < 2:
        return True
    elif((5 <= j <= 20) or (26 <= j <= 41) or (43 <= j <= 46)) and b < 1:
        return True
    else:
        return False

def decode_bits(bitstring, size, symbol_option, code_option):

    sym2bit = np.array([0, 2, 1, 3])
    sym3bit = np.array([[1, 4, 0, 5, 2, 6, 3, 7], [-1, 3, 0, 4, 1, 5, 2, 6]])
    sym4bit = np.array([[10, 1, 3, 6, 2, 5, 9, 12, 0, 8, 7, 13, 4, 14, 11, 15], [-1, 1, 3, 6, 2, 5, 9, 11, 0, 8, 7, 12, 4, 13, 10, 14]])

    index, skip = rle.read_tree(decode_trees[size-2][code_option], bitstring)
    if(skip == -1):
        return ''

    if(size == 2):
        word = [i for i, x in enumerate(sym2bit) if x == index][0]
        return format(word, '02b')

    if(size == 3):
        word = [i for i, x in enumerate(sym3bit[symbol_option]) if x == index][0]
        return format(word, '03b')

    if(size == 4):
        word = [i for i, x in enumerate(sym4bit[symbol_option]) if x == index][0]
        return format(word, '04b')


def stage_0(blocks, b, q):
    for i in range(len(blocks)):
        if(3 <= b < q):
            blocks[i].dc |= int(readb(1)) << b

def stage_1(blocks, b, q, code_words):

    for i in range(len(blocks)):
        if blocks[i].bitAC < b:
            continue
        #if(i == 6):
            #print(format(blocks[i].tran_p, '03b'), blocks[i].bitAC, i)
        #Expected length of types(P)
        num_parents = 3
        for k in range(2, -1, -1):
            if(blocks[i].tran_p >> k & 1) or subband_lim((2-k)*21, b):
                num_parents -= 1
        if(num_parents == 0):
            continue

        #Save 3bit codeword for gaggle
        if(code_words[1] == -1 and num_parents == 3):
            code_words[1] = int(readb(2), 2)
            print("|",format(code_words[1], '02b'),"|",sep='', end='')
        #Save 2bit codeword for gaggle
        elif(code_words[0] == -1 and num_parents == 2):
            code_words[0] = int(readb(1), 2)
            print("|",format(code_words[0], '01b'),"|",sep='', end='')

        elif(num_parents == 1):
            decoded = int(readb(1), 2)
            print("[",decoded,"]",sep='',end='')
            if(decoded == 1):
                blocks[i].tran_p = 7
                print("{",readb(1),"}", sep='', end='')
            continue

        #Read bits until code matches
        bitstring = readb(1)
        decoded = decode_bits(bitstring, num_parents, 0, code_words[num_parents - 2])
        while(decoded == ''):
            bitstring += readb(1)
            decoded = decode_bits(bitstring, num_parents, 0, code_words[num_parents - 2])
        decoded_value = int(decoded, 2)

        num_signs = 0
        #print("d",decoded, num_parents, format(blocks[i].tran_p,'03b'))
        offset = 0
        for j in range(num_parents):
            bit = decoded_value >> j & 1
            if(bit):
                num_signs += 1

            if(blocks[i].tran_p & 1 << j):
                offset += 1
            blocks[i].tran_p |= bit << (j + offset)
            
        #print("p", format(blocks[i].tran_p, '03b'))
        print(bitstring, end='')
        if(num_signs):
            print('{',readb(num_signs), '}',sep='',end='')
    print()



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
            if(k == 0 or index >= len(blocks)):
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


    #AC coeffs
    print("Decoding DC bits and AC coeffs")
    for b in range(bitACGlobal-1, -1, -1):
        for stage in range(2):
            for gaggle in range(0, len(blocks), 16):
                
                code_words = [-1, -1, -1]

                if(stage == 0):
                    stage_0(blocks[gaggle:gaggle+16], b, q)
                if(stage == 1):
                    print(b,end='')
                    stage_1(blocks[gaggle:gaggle+16], b, q, code_words)
