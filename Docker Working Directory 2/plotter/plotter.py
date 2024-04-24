# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 03:47:10 2024

@author: Mohammad
"""

import pika
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import awkward as ak

# Constants for plotting
MeV = 0.001
GeV = 1.0
fraction = 1.0

def on_message(ch, method, properties, body):
    # Deserialize the incoming data
    data = json.loads(body)
    ak_data = {key: ak.from_iter(data[key]) for key in data}
    
    # Call the plot_data function with the deserialized data
    plot_data(ak_data)

def plot_data(data, output_path='/app/output/histogram.png'):
    xmin = 80 * GeV
    xmax = 250 * GeV
    step_size = 5 * GeV

    bin_edges = np.arange(start=xmin, stop=xmax + step_size, step=step_size)
    bin_centres = np.arange(start=xmin + step_size / 2, stop=xmax + step_size / 2, step=step_size)

    # Convert data for histogramming
    data_x, _ = np.histogram(ak.to_numpy(data['data']['mllll']), bins=bin_edges)
    data_x_errors = np.sqrt(data_x)

    # Signal and background data
    signal_x = ak.to_numpy(data['Signal']['mllll'])
    signal_weights = ak.to_numpy(data['Signal'].totalWeight)
    signal_color = '#00cdff'  # light blue

    mc_x = []
    mc_weights = []
    mc_colors = ['#6b59d3', '#ff0000']  # colors for Z, ttbar and ZZ
    mc_labels = ['Background $Z,t\\bar{t}$', 'Background $ZZ^*$']

    # Collect MC data
    for label in mc_labels:
        mc_x.append(ak.to_numpy(data[label]['mllll']))
        mc_weights.append(ak.to_numpy(data[label].totalWeight))

    # Plotting
    plt.figure()
    main_axes = plt.gca()

    # Data points
    main_axes.errorbar(bin_centres, data_x, yerr=data_x_errors, fmt='ko', label='Data')

    # Monte Carlo histogram
    mc_heights = main_axes.hist(mc_x, bins=bin_edges, weights=mc_weights, stacked=True, color=mc_colors, label=mc_labels)
    mc_x_tot = mc_heights[0][-1]

    # Signal histogram
    main_axes.hist(signal_x, bins=bin_edges, bottom=mc_x_tot, weights=signal_weights, color=signal_color, label='Signal ($m_H$ = 125 GeV)')

    # Aesthetics
    main_axes.set_xlim(left=xmin, right=xmax)
    main_axes.set_xlabel('4-lepton invariant mass $\\mathrm{m_{4l}}$ [GeV]', fontsize=13)
    main_axes.set_ylabel('Events / 5 GeV', fontsize=13)
    main_axes.legend(frameon=False)

    plt.savefig(output_path, format='png', dpi=300)
    plt.close()

def start_consuming():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='plotting_queue')
    channel.basic_consume(queue='plotting_queue', on_message_callback=on_message, auto_ack=True)
    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    start_consuming()
