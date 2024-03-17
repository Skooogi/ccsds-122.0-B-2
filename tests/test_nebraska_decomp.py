import matplotlib.pyplot as plt
import traceback
from matplotlib.gridspec import GridSpec
import numpy as np
import os, sys
sys.path.append(os.path.abspath('../python'))
sys.path.append(os.path.abspath('../python/cython'))
import rccsds_122 as decomp

if __name__ == '__main__':

    fname_in = "../res/pattern/raw/test_image_gradient_32.raw"
    fname_out = "output.cmp"
    decomp_out = "decomp.raw"
    img_width = 32
    img_height = 32
    img_bitdepth = 8
    
    #build ccsds
    os.system('make -C ..')
    #build cython library
    os.system('(cd ../python/cython; python3 c_dwt_compile.py build_ext --inplace)')

    #build nebraska and copy to tests
    os.system('make -C ../../CCSDS/source; cp ../../CCSDS/bin/nebraska.bin nebraska.bin')

    os.system(f'./../build/ccsds.bin {fname_in} {fname_out} {img_width} {img_height} {img_bitdepth}')

    #decompress with nebraska
    os.system(f'./nebraska.bin -d {fname_out} -o {decomp_out}')

    #Decompress with python
    try:
        data_in = decomp.decompress(fname_out)
    except Exception as e:
        traceback.print_exc()
        print(":(")
        exit()

    data_org = np.fromfile(fname_in, dtype=np.uint16).reshape([img_height, img_width])
    data_out = np.fromfile(decomp_out, dtype= np.uint16 if img_bitdepth > 8 else np.uint8).reshape([img_height, img_width])
    data_out = data_out.astype(np.int32)
    print("Visualizing")
    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(2,2,figure=fig)

    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])

    ax0.set_title("Nebraska")
    ax0.imshow(data_out, cmap='gray')
    ax1.set_title("Python")
    ax1.imshow(data_in, cmap='gray')
    ax2.set_title("Original")
    ax2.imshow(data_org, cmap='gray')
    ax3.set_title("Error")
    ax3.imshow(data_org-data_out, cmap='gray')

    diff = data_out-data_in

    x = 0
    xw = 8
    y = 0
    yw = 8
    print("nebraska")
    print(data_out[y:y+yw,x:x+xw])
    print("python")
    print(data_in[y:y+yw,x:x+xw])

    #dmax = max(diff.flatten()) 
    #dmin = min(diff.flatten())

    #diff = diff - dmin
    print("diff")
    print(diff[y:y+yw,x:x+xw])
    print(diff.min(), diff.max())

    err = data_org - data_out
    print("Error from original")
    print(err[y:y+yw,x:x+xw])
    print(err.min(), err.max())


    error = 0
    for i in range(img_height):
        for j in range(img_width):
            error += diff[i][j]**2
    print("mse", error/(img_height*img_width))

    #ax2.set_title("Difference")
    #ax2.imshow(diff, cmap='gray')
    plt.show()

