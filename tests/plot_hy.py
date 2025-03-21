from cycler import cycler
from matplotlib import pyplot as plt
plt.rcParams.update({'font.size': 22})
plt.rcParams.update({'lines.markersize' : 12})
import numpy as np
import pandas as pd

filter_keep = ['AIS', 'D2v5']
filter_discard = ['STV', 'TV', 'HyRes', 't0', 'W3D', 'FORPDN', 'LRMR']

VIS = 1
DIFF = 0

def filter_name(x):
    return x in filter_keep

if __name__ == "__main__":
    try:
        with open("results_combined.csv", "r") as fp:
            lines = fp.readlines()
    except:
        print("No file named 'results.csv' found!")
        exit()


    #Data is stored as:
    #Filename, Category, Width, Height, Bitdetph, Compression ratio
    lines = lines[2:]
    lines.sort()
    #[print(x) for x in lines[:20]]

    data_lines = []
    avg = 0
    prev = 0
    org_line = lines[0]

    for i in range(len(lines)):
        line_data = lines[i][:-1].split(',')
        num = int(line_data[0].split("_")[1].split('.')[0])

        if(num >= prev and i < len(lines)-1):
            org_line = line_data
            prev = num
            avg += float(line_data[-1])

        else:
            if(prev%2): #indexing from 0
                prev+=1
            if(i == len(lines)-1):
                avg += float(line_data[-1])
            avg /= (prev)

            org_line[-1] = f'{avg}'
            data_lines.append(org_line)

            avg = float(line_data[-1])
            prev = num
            org_line = line_data

    data = []
    for i in data_lines:
        diff_split = i[0].split("_")
        name = diff_split[0]
        exposure = float(name.split("ms")[0].split("-")[-1])
        distance = int(name.split("km")[0].split("-")[-1])
        filter = '_'.join(name.split("ms")[1][1:].split('.')[:2])
        vis = 1 if "vis" in name else 0
        diff = 1 if "diff" in name else 0

        if("noiseless" in name):
            filter += "noiseless"
        if("D1D2" in name):
            name = "D1v5D2"
        name = name.split('-')[0]
        data.append([name, vis, diff, distance, exposure, filter, float(i[-1])])

    df = pd.DataFrame(data)
    df.columns = [
        "Name",
        "VIS",
        "DIFF",
        "Distance",
        "Exposure",
        "Filter",
        "Compression ratio"]


    #df = df.sort_values(
    #    ["Name", "VIS", "Distance", "Exposure", "Filter", "diff_num"],
    #    ascending=[True,True,True,True,True,True])

    #Average diff images
    #df.groupby(["Name", "VIS", "Distance", "Exposure", "Filter"])
    filters = list(set(df['Filter'].tolist()))
    filters.sort()
    #print(df[(df['Filter']=="CCSDS") & (df["VIS"] == 1)].sort_values(["Name", "Distance", "Exposure"]))

    #Prints non filered and non differentially encoded as reference
    if(DIFF):
        temp = df[(df['Filter']=="") & (df["VIS"] == VIS) & (df["DIFF"] == 0)].sort_values(["Name", "Distance", "Exposure"])
        vls = (np.array(temp['Compression ratio'].tolist()))
        plt.plot(np.array(range(len(vls)))+1, vls*100, "x-", label="no filter")

    vals = []
    for i,filter in enumerate(filters):
        #print(i,filter)
        temp = df[(df['Filter']==filter) & (df["VIS"] == VIS) & (df["DIFF"] == DIFF)].sort_values(["Name", "Distance", "Exposure"])
        print(temp)
        check = (np.array(temp['Compression ratio'].tolist()))
        if(len(check) != 21):
            check = check[1::2]

        vals.append(check)


    for i,filter in enumerate(filters):
        #if("noiseless" in filter):
        #    continue
        if("TV" in filter):
            continue
        if("FORPDN" == filter):
            continue
            

        label = ""
        if(DIFF):
            label += f'diff+'
        if(filter != ""):
            if("FORPDN" in filter):
                label += "FORPDN"
            else:
                label += filter
        else:
            label += "no filter"

        if(len(vals[i]) != 0):
            if(i == 0 and DIFF):
                plt.plot(np.array(range(len(vals[i])))+1, vals[i]*100, "x-", label=label, color="tab:cyan")
            else:
                plt.plot(np.array(range(len(vals[i])))+1, vals[i]*100, "x-", label=label)


    df.to_csv("ccsds_processed.csv", sep=";")

    plt.title(f'CCSDS lossless compression ratio \n({'differential ' if DIFF else ''}{'VIS' if VIS else 'NIR'})', pad = 20)

    plt.ylim([0, 60 if VIS else 80])
    plt.ylabel("Compressed file size (% of the original)")
    plt.xlim([0, 22])
    plt.xticks(range(1,22,3),labels=range(1,8))
    plt.xlabel("Image index")

    plt.grid()
    plt.legend(prop={'size':20})#, ncols=2, loc=(0.005, 0.005))
    plt.show()
