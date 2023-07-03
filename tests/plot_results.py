import numpy as np
import matplotlib.pyplot as plt
import os


if __name__ == '__main__':

    results = []
    names = []

    for filename in os.listdir("results"):
        if (filename[-4:] != ".res"):
            continue
        print("found results for: "+filename[:-4]+'!')
        temp = np.fromfile("results/"+filename).reshape(-1, 4)
        results.append(temp)
        names.append(filename[:-4])
        
    names.reverse()

    n = [32, 64, 128, 256, 512, 1024, 2048, 4096]
    fig, ax = plt.subplots(2, 1)
    ax[0].set_title("Version comparison")
    ax[0].set_xlabel("image side length (px)")
    ax[0].set_ylabel("time (s)")
    ax[0].grid()

    versions = []
    version_ops = []
    for i in range(len(results)):
        time, inst, cache, ops = zip(*results[i])
        ax[0].plot(n, time, label=names[i], **{'markerfacecolor': 'white', 'marker': 'o'})

        version_ops.append(ops[-1])

        print(f'v{i}:')
        print(f'\tinstr/cycle\t{inst[-1]:.2f}')
        print(f'\tmiss/branch\t{cache[-1]:.2f}%')
        print(f'\tops/s\t\t{ops[-1]:.1f}')
    
    ax[0].legend()

    ax[1].bar(names, version_ops)
    ax[1].set_xlabel("version")
    ax[1].set_ylabel("billion operations / s")
    ax[1].yaxis.set_ticks(np.arange(0, 16, 1))

    plt.show()
