from cycler import cycler
from matplotlib import pyplot as plt
import numpy as np

plt.rcParams['axes.prop_cycle'] = cycler('color', plt.get_cmap('Set3').colors)

if __name__ == "__main__":
    try:
        with open("results.csv", "r") as fp:
            lines = fp.readlines()
    except:
        print("No file named 'results.csv' found!")
        exit()


    #Data is stored as:
    #Filename, Category, Width, Height, Bitdetph, Compression ratio
    data_lines = []
    for i in range(2, len(lines)):
        data_lines.append(lines[i][:-1].split(','))

    #Group data by group
    data = {}
    for filename, group, width, height, bitdepth, ratio in data_lines:
        data.setdefault(group, []).append([filename, int(width), int(height), int(bitdepth), float(ratio)])

    x = np.arange(len(data.keys()))
    category_index = 0
    width = 0.8
    max_length = -1
    for category, results in data.items():
        length = len([row[-1] for row in results])
        max_length = max(length, max_length)


    offset = width/max_length
    for category, results in data.items():
        values = [row[-1] for row in results]
        names = [row[0] for row in results]

        for i,value in enumerate(values):
            x_position = x[category_index]+len(values)*offset/2 - offset/2 -offset*i

            plt.bar(x_position, value*100, width=offset)
            plt.text(x_position, 1, names[i], color='black',ha='center', va='bottom', rotation=90, fontsize=10)

        category_index += 1

    plt.axhline(75, color='r', linestyle='--')

    plt.xticks(x, data.keys())
    plt.yticks(range(0,130,10))
    plt.grid()
    plt.ylabel("Compressed filesize/original filesize (%)")
    plt.xlabel("Category")
    plt.title(lines[0])
    plt.show()
