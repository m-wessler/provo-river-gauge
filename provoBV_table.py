#!/uufs/chpc.utah.edu/sys/installdir/anaconda3/2018.12/bin/python

with open('/uufs/chpc.utah.edu/common/home/u1070830/rio_project/bvlog.txt', 'r+') as rfp:
    with open('/uufs/chpc.utah.edu/common/home/u1070830/public_html/rivers/provo/bvlog.csv', 'w+') as wfp:

        csvdata = rfp.readlines()
        lines = len(csvdata)
        maxlines = 12 * 24 # 12x hour * 24 hours
        
        wfp.write(csvdata[0])

        if lines <= maxlines:
            [wfp.write(line) for line in csvdata[1:][::-1]]
                
        else:
            for line in csvdata[-maxlines:][::-1]:
                wfp.write(line)