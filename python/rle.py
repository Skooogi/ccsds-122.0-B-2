import numpy as np
import math
import struct
import sys
import filecmp

class NodeTree(object):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def children(self):
        return self.left, self.right

    def __str__(self):
        return self.left, self.right

def huffman_code_tree(node, binString=''):
    '''
    Function to find Huffman Code
    '''
    if type(node) is np.int64:
        return {node: binString}
    (l, r) = node.children()
    d = dict()
    d.update(huffman_code_tree(l, binString + '0'))
    d.update(huffman_code_tree(r, binString + '1'))
    return d

def read_tree(node, binstr):

    bits_traversed = 0
    curr_node = node
    while type(curr_node) != np.int64 and len(binstr) != 0:
        if(binstr[0] == '0'):
            curr_node = curr_node.left
        else:
            curr_node = curr_node.right

        bits_traversed += 1
        binstr = binstr[1:]

    return curr_node, bits_traversed


def regen_tree(node, value, binstr):

    curr_node = node

    while len(binstr) != 1:
        if(binstr[0] == '1'):
            if(curr_node.right == None):
                curr_node.right = NodeTree()
            curr_node = curr_node.right
        else:
            if(curr_node.left == None):
                curr_node.left = NodeTree()
            curr_node = curr_node.left
        binstr = binstr[1:]

    if(binstr == '0'):
        curr_node.left = value

    else:
        curr_node.right = value

def make_tree(nodes):
    '''
    Function to make tree
    :param nodes: Nodes
    :return: Root of the tree
    '''
    while len(nodes) > 1:
        (key1, c1) = nodes[-1]
        (key2, c2) = nodes[-2]
        nodes = nodes[:-2]
        node = NodeTree(key1, key2)
        nodes.append((node, c1 + c2))
        nodes = sorted(nodes, key=lambda x: x[1], reverse=True)
    return nodes[0][0]

def out_bits(fp, data):
    
    size = len(data)
    mod = size%8
    for i in range(0, len(data)-mod, 8):
        fp.write(struct.pack('B', int(data[i:i+8],2)))
    if(mod > 0):
        fp.write(struct.pack('B', int(data[len(data)-mod:len(data)]+"0"*(8-mod),2)))

def compress(filein, fileout):

    num = np.array([[x, 0] for x in range(256)])
    with open(filein, "rb") as f:
        while (byte := f.read(1)):
            num[int.from_bytes(byte, "big")][1] += 1

    freq = dict(num)
    freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    node = make_tree(freq)

    encoding = huffman_code_tree(node)
    encoding = sorted(encoding.items(), key=lambda x: (len(x[1]), x[0]), reverse=False)
    encoding = dict(encoding)

    bitstring = ""
    fp = open(fileout, "wb")
    curr = '-1'
    for i in encoding:
        length = len(encoding[i])
        curr = format(int(curr, 2) + 1, f'0{len(curr)}b')
        if(len(curr) < length):
           curr += '0'*(length - len(curr))
        encoding.update({int(i): curr})

    for i in range(256):
        bitstring += format(len(encoding[i]), '04b')

    out_bits(fp, bitstring)

    bitstring = ""
    with open(filein, "rb") as f:
        while (byte := f.read(1)):
            bitstring += encoding[int.from_bytes(byte, "big")]
    padding = format(8-len(bitstring)%8, '08b')
    out_bits(fp,padding+bitstring)
    fp.close()

def uncompress(filein, fileout):

    #Read file
    data = 0
    with open(filein, "rb") as f:
        data = f.read()
    
    encoding = np.array([[x, 0] for x in range(256)])
    for i in range(0, 256, 2):
        byte = data[int(i/2)]
        encoding[i][1] = (byte >> 4) & 0xf
        encoding[i+1][1] = byte & 0xf
    data = data[128:]
    padding = data[0]
    data = data[1:]
    
    encoding = dict(sorted(encoding, key=lambda x: (x[1], x[0]), reverse=False))
    curr = '-1'
    huffman_tree = NodeTree()
    for i in encoding:
        length = encoding[i]
        curr = format(int(curr, 2) + 1, f'0{len(curr)}b')
        if(len(curr) < length):
           curr += '0'*(length - len(curr))
        encoding.update({int(i): curr})
        regen_tree(huffman_tree, i, encoding[i])
        #print(i, encoding[i])


    with open(fileout, "wb") as f:
        with open("output.cmp", "rb") as fp:

            binstr = ''
            for i in range(len(data)):
                binstr += format(data[i], '08b')
                if(i == len(data)-1):
                    binstr = binstr[:-padding]

                value, skip = read_tree(huffman_tree, binstr)
                while type(value) == np.int64:
                    binstr = binstr[skip:]
                    if(fp.read(1) != struct.pack('B', value)):
                        print(value, skip)
                        print(fp.read(1), struct.pack('B', value), value)
                    f.write(struct.pack('B', value))
                    value, skip = read_tree(huffman_tree, binstr)

if __name__ == '__main__':
    args = sys.argv
    if(len(args) > 3 and args[1] == "compress"):
        compress(args[2], args[3])
    elif(len(args) > 3 and args[1] == "uncompress"):
         uncompress(args[2], args[3])

    else:
         print("Input error")
    

