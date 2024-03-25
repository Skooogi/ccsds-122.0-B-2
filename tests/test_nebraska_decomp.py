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

    fname_in = "../res/noise/raw/test_image_new_noise_32.raw"
    #fname_in = "temp_orig_26.raw"
    fname_out = "output.cmp"
    decomp_out = "decomp.raw" #786x604 -> 792x608
    img_width = 32
    img_height = 32
    img_bitdepth = 16
    
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
        python_image = np.ones([img_height, img_width]) * -1

    original_image = np.fromfile(fname_in, dtype=np.uint16).reshape([img_height, img_width])
    nebraska_image = np.fromfile(decomp_out, dtype= np.int16 if img_bitdepth >= 8 else np.uint8).reshape([img_height, img_width])
    nebraska_image = nebraska_image.astype(np.int32)
    print("Visualizing")
    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(2,3,figure=fig)

    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])
    ax4 = fig.add_subplot(gs[0, 2])
    ax5 = fig.add_subplot(gs[1, 2])

    ax0.set_title("Nebraska")
    ax0.imshow(nebraska_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax1.set_title("Error")
    ax1.imshow(original_image - nebraska_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax2.set_title("Original")
    ax2.imshow(original_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax3.set_title("Nebraska - Python")
    ax3.imshow(nebraska_image-python_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax4.set_title("Python")
    ax4.imshow(python_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    ax5.set_title("Error")
    ax5.imshow(original_image - python_image, cmap='gray', interpolation='none', extent=[0, img_width, img_height, 0])
    mpl.cursor(hover=True)

    diff_np = nebraska_image-python_image
    diff_op = original_image - python_image
    diff_on = original_image - nebraska_image


    x = 0
    xw = 8
    y = 0
    yw = 8
    print("nebraska")
    print(nebraska_image[y:y+yw,x:x+xw])
    print("python")
    print(python_image[y:y+yw,x:x+xw])

    #dmax = max(diff_np.flatten()) 
    #dmin = min(diff_np.flatten())

    #diff_np = diff - dmin
    print("diff_np")
    print(diff_np[y:y+yw,x:x+xw])
    print(diff_np.min(), diff_np.max())

    print("Nebraska error_np from original")
    print(diff_on[y:y+yw,x:x+xw])
    print(diff_on.min(), diff_on.max())

    error_np = 0
    error_op = 0
    error_on = 0
    for i in range(img_height):
        for j in range(img_width):
            error_np += diff_np[i][j]**2
            error_op += diff_op[i][j]**2
            error_on += diff_on[i][j]**2
            
    mse_np = error_np/(img_height*img_width)
    mse_op = error_op/(img_height*img_width)
    mse_on = error_on/(img_height*img_width)
    psnr_np = 10*np.log10((2**img_bitdepth-1)**2/mse_np) if mse_np != 0 else 0
    psnr_op = 10*np.log10((2**img_bitdepth-1)**2/mse_op) if mse_op != 0 else 0
    psnr_on = 10*np.log10((2**img_bitdepth-1)**2/mse_on) if mse_on != 0 else 0

    print("PSNR diff\t", psnr_np)
    print("PSNR python\t", psnr_op)
    print("PSNR nebraska\t", psnr_on)

    with open("PSNR.txt", 'a') as f:
        f.write(str(psnr_np)+',')
        if(len(sys.argv) > 1 and sys.argv[1] == 'f'):
            f.write(str(psnr_op)+',f\n')
        else:
            f.write(str(psnr_op)+'\n')

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
        ax0.axvline(x=84, linestyle='--', color='red', label='Checker32')
        ax0.axvline(x=102, linestyle='--', color='red', label='Noise32')
        ax0.axvline(x=288, linestyle='--', color='red', label='Generated noise 32')
        ax0.plot(range(len(temp[d1mask])), data_1[d1mask], figure=g, label='PSNR python/nebraska')
        ax0.plot(range(len(temp[d2mask])), data_2[d2mask], figure=g, label='PSNR python lossless')
        ax0.grid()
        ax0.legend()

        ax1.set_title("Full")
        ax1.axvline(x=36, linestyle='--', color='red', label='Checker32')
        ax1.axvline(x=40, linestyle='--', color='red', label='White32')
        ax1.axvline(x=41, linestyle='--', color='red', label='Black32')
        ax1.axvline(x=45, linestyle='--', color='red', label='Noise32')
        ax1.plot(range(len(temp[d3mask])), data_3[d3mask], figure=g, label='PSNR python/nebraska')
        ax1.plot(range(len(temp[d4mask])), data_4[d4mask], figure=g, label='PSNR python lossless')
        ax1.grid()
        ax1.legend()

    plt.show()

