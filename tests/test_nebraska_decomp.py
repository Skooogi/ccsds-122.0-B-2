from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import mplcursors as mpl
import numpy as np
import os, sys
sys.path.append(os.path.abspath('../python'))
sys.path.append(os.path.abspath('../python/cython'))
import rccsds_122 as decomp
import traceback

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
        python_image = decomp.decompress(fname_out)
    except Exception as e:
        traceback.print_exc()
        print(":(")
        exit()

    original_image = np.fromfile(fname_in, dtype=np.uint16).reshape([img_height, img_width])
    nebraska_image = np.fromfile(decomp_out, dtype= np.uint16 if img_bitdepth > 8 else np.uint8).reshape([img_height, img_width])
    nebraska_image = nebraska_image.astype(np.int32)
    print("Visualizing")
    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(2,2,figure=fig)

    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])

    ax0.set_title("Nebraska")
    ax0.imshow(nebraska_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax1.set_title("Python diff")
    ax1.imshow(nebraska_image - python_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax2.set_title("Original")
    ax2.imshow(original_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax3.set_title("Error")
    ax3.imshow(original_image-python_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    mpl.cursor(hover=True)
    diff = nebraska_image-python_image

    x = 0
    xw = 8
    y = 0
    yw = 8
    print("nebraska")
    print(nebraska_image[y:y+yw,x:x+xw])
    print("python")
    print(python_image[y:y+yw,x:x+xw])

    #dmax = max(diff.flatten()) 
    #dmin = min(diff.flatten())

    #diff = diff - dmin
    print("diff")
    print(diff[y:y+yw,x:x+xw])
    print(diff.min(), diff.max())

    err = original_image - nebraska_image
    print("Nebraska error from original")
    print(err[y:y+yw,x:x+xw])
    print(err.min(), err.max())


    diff_gl = original_image - python_image
    diff_imp = nebraska_image - python_image

    error = 0
    error_gl = 0
    error_imp = 0
    for i in range(img_height):
        for j in range(img_width):
            error += diff[i][j]**2
            error_gl += diff_gl[i][j]**2
            error_imp += diff_imp[i][j]**2
            
    mse = error/(img_height*img_width)
    mse_gl = error_gl/(img_height*img_width)
    mse_imp = error_imp/(img_height*img_width)
    psnr = 10*np.log10((2**img_bitdepth-1)**2/mse) if mse != 0 else 0
    psnr_gl = 10*np.log10((2**img_bitdepth-1)**2/mse_gl) if mse_gl != 0 else 0
    psnr_imp = 10*np.log10((2**img_bitdepth-1)**2/mse_imp) if mse_imp != 0 else 0

    print("PSNR nebraska", psnr)
    print("PSNR python", psnr_gl)
    print("PSNR diff", psnr_imp)

    with open("PSNR.txt", 'a') as f:
        f.write(str(psnr_imp)+',')
        if(len(sys.argv) > 1 and sys.argv[1] == 'f'):
            f.write(str(psnr_gl)+',f\n')
        else:
            f.write(str(psnr_gl)+'\n')

    with open("PSNR.txt") as f:
        temp = np.array(f.read().split('\n')[:-1])
        data_1 = np.array([i.split(',')[0] if len(i.split(',')) != 3 else None for i in temp]).astype(float)
        d1mask = np.isfinite(data_1)

        data_2 = np.array([i.split(',')[1] if len(i.split(',')) != 3 else None for i in temp]).astype(float)
        d2mask = np.isfinite(data_2)

        data_3 = np.array([i.split(',')[0] if len(i.split(',')) == 3 else None for i in temp]).astype(float)
        d3mask = np.isfinite(data_3)

        data_4 = np.array([i.split(',')[1] if len(i.split(',')) == 3 else None for i in temp]).astype(float)
        d4mask = np.isfinite(data_4)

        g = plt.figure(2) 
        fs = GridSpec(2,1,figure=g)
        ax0 = g.add_subplot(fs[0, 0])
        ax1 = g.add_subplot(fs[1, 0])

        ax0.set_title("Partial")
        ax0.plot(range(len(temp[d1mask])), data_1[d1mask], figure=g, label='PSNR python/nebraska')
        ax0.plot(range(len(temp[d2mask])), data_2[d2mask], figure=g, label='PSNR python lossless')
        ax0.grid()
        ax0.legend()

        ax1.set_title("Full")
        ax1.plot(range(len(temp[d3mask])), data_3[d3mask], figure=g, label='PSNR python/nebraska')
        ax1.plot(range(len(temp[d4mask])), data_4[d4mask], figure=g, label='PSNR python lossless')
        ax1.grid()
        ax1.legend()

        

    plt.show()
    #ax2.set_title("Difference")
    #ax2.imshow(diff, cmap='gray')

