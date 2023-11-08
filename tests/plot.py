from matplotlib import pyplot as plt
import numpy as np

if __name__ == "__main__":
    
    with open("results.txt", "r") as fp:
        lines = fp.readlines()

    i = -1
    names = []
    values = np.array([], dtype=float)
    for line in lines:
        line = line[:-1]
        if 'x' in line:
            i += 1
            names.append(line)
        else:
            values = np.append(values, float(line)*100)

    values = values.reshape(len(names), len(values)//len(names))

    x = np.array(range(7))
    x = x + 1

    print("Average compression difference from padding")
    print((values[1]/values[0])*100-100)

    plt.bar(x-0.3, values[0], width=0.2, color='gold', label=names[0])
    plt.bar(x-0.1, values[1], width=0.2, color='turquoise', label=names[1])
    plt.bar(x+0.1, values[2], width=0.2, color='darkturquoise', label=names[2])
    plt.bar(x+0.3, values[3], width=0.2, color='lightseagreen', label=names[3])
    plt.grid()
    plt.yticks(np.arange(0, 110, 10))
    plt.ylim(0,100)
    plt.title("Average compression ratio of 100 strip images")
    plt.ylabel("Compressed filesize/original filesize (%)")
    plt.xlabel("Image index in res/space folder")
    plt.legend()
    plt.show()
