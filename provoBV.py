#!/uufs/chpc.utah.edu/sys/installdir/anaconda3/2018.12/bin/python

import os
import numpy as np
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

def get_bvflow(dd):
    
    inflows = ['Deer Creek Penstock #1 Flow', 
                'Deer Creek Penstock #2 Flow', 
                'Deer Creek Spillway Flow']

    diversions = ['Deer Creek Salt Lake Aqueduct Flow']

    # Can set an offset/bias correct here
    bvflow = 0
    
    # print('%s\n'%datadict['Deer Creek Penstock #1 Flow']['time'][-1])
    print('%s'%datadict['Deer Creek Penstock #2 Flow']['time'][-1], end=', ')

    for k in inflows + diversions:

        if k in inflows:
            bvflow += dd[k]['value'][-1]
            # print('%s:\t\t+%.0f cfs'%(k, dd[k]['value'][-1]))
            print('%.0f'%dd[k]['value'][-1], end=', ')

        elif k in diversions:
            bvflow -= dd[k]['value'][-1]
            # print('%s:\t-%.0f cfs'%(k, dd[k]['value'][-1]))
            print('-%.0f'%dd[k]['value'][-1], end=', ')

    # Try to find a source for the actual power plant diversion in realtime...
    # for now assume max of 510 cfs
    maxpower = 510
    powergen = maxpower if bvflow > maxpower else bvflow
    bvflow -= powergen
    print('-%.0f'%powergen, end=', ')

    # print('Deer Creek Power Generation:\t\t-%.0f cfs'%powergen)
    
    # print('\nEstimated BV Flow:\t\t\t%.0f cfs'%bvflow)
    print('%.0f'%(bvflow))
    
    return round(bvflow, 2)

def gen_plot(dd):

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    plt.rcParams.update({'font.size': 16})
    plt.rcParams.update({'figure.autolayout': True})

    plotkeys = ['Deer Creek Penstock #1 Flow', 
                'Deer Creek Penstock #2 Flow', 
                'Deer Creek Spillway Flow', 
                'Deer Creek Salt Lake Aqueduct Flow', 
                'Provo River Bridal Veil Flow']

    fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(24,12), facecolor='w')
    fig.subplots_adjust(wspace=0, hspace=0.05)
    ax1, ax2 = ax

    for k in plotkeys:
        ax = ax2 if k == 'Provo River Bridal Veil Flow' else ax1
        
        x, y = dd[k]['time'], dd[k]['value']

        if 'Spillway' in k:
            ax.scatter(x, y, marker='*', color='r', s=200, label=k)
        else:
            ax.plot(x, y, linewidth='3', label=k)
        
    powergen = 515.
    ax1.axhline(y=powergen, linewidth=3, label='Power Generation [Estimated Max]', c='k')
        
    for ax in [ax1, ax2]:
        ax.grid(True)
        ax.set_ylabel('\nFlow [cfs]\n')
        ax.set_ylim([0 , 1600])
    
    # t0 = dd['Provo River Bridal Veil Flow']['time'][0]
    # t0 = t0 - timedelta(minutes=t0.minute % 5, seconds=t0.second, microseconds=t0.microsecond)
    # t0 = t0 + timedelta(minutes=5)
        
    tf = dd['Provo River Bridal Veil Flow']['time'][-1]
    tf =  tf - timedelta(minutes=tf.minute % 5, seconds=tf.second, microseconds=tf.microsecond)
    
    t0 = tf - timedelta(days=2)
    
    ax.set_xlim([t0, tf])
    
    mins = mdates.HourLocator(interval=3)
    fmt = mdates.DateFormatter('%m/%d %I:%M %p')
    ax.xaxis.set_major_locator(mins)
    ax.xaxis.set_major_formatter(fmt)
    plt.xticks(rotation=70)
        
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        
    ax2.set_xlabel('\nDate & Time\n')

    # Put a legend to the right of the current axis
    ax1.legend(loc='upper left', bbox_to_anchor=(0.773, 1.43))
    ax2.legend(loc='upper right')
        
    ax1.set_title('Provo River Flow Data\n\nUpdated %s\nEstimated: %.0f cfs\n'%(
        dd['Provo River Bridal Veil Flow']['time'][-1].strftime('%m/%d/%y %H:%M'), 
        dd['Provo River Bridal Veil Flow']['value'][-1]))

    webdir = '/uufs/chpc.utah.edu/common/home/u1070830/public_html/rivers/provo/'
    plt.savefig(webdir + 'provoBV_current.png', dpi=300)


if __name__ == '__main__':

    df = '/uufs/chpc.utah.edu/common/home/u1070830/rio_project/data/provoBV.npy'
    new = False if os.path.isfile(df) else True

    try:
        r = requests.get('https://www.prwua.org/water-operations/live-SCADA-system-data.php')
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find(id='livescada')
        rows = table.find_all('tr')

    except:
        # Guards against failed scrape
        print('scrape failed')
        pass

    else:
        if new:
            datadict = {}
        else:
            datadict = np.load(df)[()]

        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]

            sid = cols[0]
            site = cols[3]

            time = datetime.strptime(cols[1], '%m/%d/%Y %I:%M:%S %p')
            value = float(cols[2])
            valtype = site.split(' ')[-1].lower()

            if new:
                datadict[site] = {'sid':sid, 'type':valtype, 'time':[time], 'value':[value]}
                
            else:
                # print(site, valtype, time, value)
                try:
                    datadict[site]['time'].append(time)
                    datadict[site]['value'].append(value)
                except KeyError:
                    # print(site, valtype, 'no value')
                    pass
                    
        if new:
            datadict['Provo River Bridal Veil Flow'] = {'sid':'BV_EST', 'type':'flow', 
                                                        'time':[datadict['Deer Creek Penstock #2 Flow']['time'][-1]],
                                                        'value':[get_bvflow(datadict)]}
        else:
            datadict['Provo River Bridal Veil Flow']['time'].append(datadict['Deer Creek Penstock #2 Flow']['time'][-1])
            datadict['Provo River Bridal Veil Flow']['value'].append(get_bvflow(datadict))
                
        np.save(df, datadict)

        gen_plot(datadict)
