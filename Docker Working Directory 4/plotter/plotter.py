# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 10:42:08 2024
@author: Mohammad
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import pika
import pickle  # Replace json with pickle
import awkward as ak
from time import sleep

output_dir = '/app/output'
# Constants for unit conversion
GeV = 1.0
MeV = 0.001

def connect_to_rabbitmq():
    """Establish a connection to RabbitMQ server with retry logic."""
    credentials = pika.PlainCredentials(os.getenv('RABBITMQ_DEFAULT_USER', 'user'),
                                        os.getenv('RABBITMQ_DEFAULT_PASS', 'password'))
    host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    port = int(os.getenv('RABBITMQ_PORT', '5672'))

    for _ in range(5):  # Retry up to 5 times
        try:
            parameters = pika.ConnectionParameters(host=host, port=port, virtual_host='/',
                                                   credentials=credentials, connection_attempts=3,
                                                   retry_delay=5, socket_timeout=5)
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError as e:
            print("Failed to connect to RabbitMQ, retrying...")
            sleep(5)
    raise Exception("Failed to connect to RabbitMQ after multiple attempts.")

def check_all_containers_finished():
    """Check if all containers have finished processing."""
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='completion_queue', durable=True)
    
    def completion_callback(ch, method, properties, body):
        nonlocal count
        count += 1
        print(f"Received completion message {count}/4")
        if count >= 4:  # Adjusted to match the number of processing containers
            channel.stop_consuming()

    count = 0
    channel.basic_consume(queue='completion_queue', on_message_callback=completion_callback, auto_ack=True)
    print('Waiting for all processing containers to complete...')
    channel.start_consuming()
    connection.close()
    print('All processing containers have completed. Proceeding to consume plot data.')

def start_consuming():
    """Start consuming messages from RabbitMQ to plot."""
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='plotting_queue', durable=True)
    channel.basic_consume(queue='plotting_queue', on_message_callback=plot_callback, auto_ack=True)
    print('Waiting for plot data messages. To exit press CTRL+C')
    channel.start_consuming()

def plot_callback(ch, method, properties, body):
    """Callback function to process received messages and plot data."""
    try:
        data = pickle.loads(body)  # Use pickle to deserialize data
        print("Plotting data...")
        plot_data(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Manually send the acknowledgment
        print(f"Data plotted and acknowledged for delivery tag: {method.delivery_tag}")
    except Exception as e:
        print(f"Failed to plot data: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def plot_data(data):
    """Plot data using the same style and annotations as the original script."""
    xmin = 80 * GeV
    xmax = 250 * GeV
    step_size = 5 * GeV

    bin_edges = np.arange(start=xmin, stop=xmax+step_size, step=step_size)
    bin_centres = np.arange(start=xmin+step_size/2, stop=xmax+step_size/2, step=step_size)

    data_x, _ = np.histogram(ak.to_numpy(data['data']['mllll']), bins=bin_edges)
    data_x_errors = np.sqrt(data_x)

    signal_x = ak.to_numpy(data['Signal']['mllll'])
    signal_weights = ak.to_numpy(data['Signal']['totalWeight'])
    signal_color = "#00cdff"  # Light blue for signal

    mc_x = []
    mc_weights = []
    mc_colors = []
    mc_labels = []

    for key, value in data['background'].items():
        mc_x.append(ak.to_numpy(value['mllll']))
        mc_weights.append(ak.to_numpy(value['totalWeight']))
        mc_colors.append(value['color'])
        mc_labels.append(key)

    plt.figure(figsize=(10, 7))
    main_axes = plt.gca()

    main_axes.errorbar(x=bin_centres, y=data_x, yerr=data_x_errors, fmt='ko', label='Data')
    mc_heights = main_axes.hist(mc_x, bins=bin_edges, weights=mc_weights, stacked=True, color=mc_colors, label=mc_labels)
    mc_x_tot = mc_heights[0][-1]

    mc_x_err = np.sqrt(np.histogram(np.hstack(mc_x), bins=bin_edges, weights=np.hstack(mc_weights)**2)[0])
    main_axes.hist(signal_x, bins=bin_edges, bottom=mc_x_tot, weights=signal_weights, color=signal_color, label='Signal ($m_H$ = 125 GeV)')

    main_axes.bar(bin_centres, 2 * mc_x_err, alpha=0.5, bottom=mc_x_tot - mc_x_err, color='none', hatch="////", width=step_size, label='Stat. Unc.')

    main_axes.set_xlim(left=xmin, right=xmax)
    main_axes.set_xlabel(r'4-lepton invariant mass $\mathrm{m_{4l}}$ [GeV]', fontsize=13)
    main_axes.set_ylabel('Events / ' + str(step_size) + ' GeV', fontsize=13)

    plt.text(0.05, 0.93, 'ATLAS Open Data', transform=main_axes.transAxes, fontsize=13)
    plt.text(0.05, 0.88, 'for education', transform=main_axes.transAxes, style='italic', fontsize=8)
    plt.text(0.05, 0.82, '$\sqrt{s}$=13 TeV,$\int$L dt = 10 fb$^{-1}$', transform=main_axes.transAxes)
    plt.text(0.05, 0.76, r'$H \rightarrow ZZ^* \rightarrow 4\ell$', transform=main_axes.transAxes)

    main_axes.legend(frameon=False)
    plot_filename = 'histogram_plot.png'
   
    # Construct the full path where the plot will be saved
    plot_path = os.path.join(output_dir, plot_filename)

    # Save the plot to the specified directory
    plt.savefig(plot_path)
    
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    start_consuming()
