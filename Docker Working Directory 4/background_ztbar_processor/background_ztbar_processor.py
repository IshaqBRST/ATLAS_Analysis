# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 10:26:52 2024
@author: Mohammad
"""

import time
import uproot
import awkward as ak
import vector
import pika
import pickle  # Import pickle for serialization
import infofile
from config import samples, tuple_path

# Constants for unit conversion
MeV = 0.001
GeV = 1.0

def connect_to_rabbitmq():
    """Establish a connection to RabbitMQ server."""
    credentials = pika.PlainCredentials('user', 'password')
    parameters = pika.ConnectionParameters('rabbitmq', 5672, '/', credentials)
    return pika.BlockingConnection(parameters)

def publish_data(data, queue_name):
    """Publish processed data to a specified RabbitMQ queue using pickle."""
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Serialize data using pickle
    pickled_data = pickle.dumps(data)
    
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=pickled_data,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    print(f"Data published to RabbitMQ queue {queue_name}")
    connection.close()
    
def send_completion_message():
    """Send a completion message to RabbitMQ."""
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='completion_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='completion_queue',
        body='Processing completed',
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        ))
    print("Sent completion message to RabbitMQ.")
    connection.close()

def read_file(path, sample):
    """Read data from ROOT file, apply cuts, calculate mass, and gather data."""
    print(f"\tProcessing: {sample}")
    start = time.time()
    data_all = []

    with uproot.open(path + ":mini") as tree:
        numevents = tree.num_entries
        for data in tree.iterate(['lep_pt', 'lep_eta', 'lep_phi', 'lep_E', 'lep_charge', 'lep_type',
                                  'mcWeight', 'scaleFactor_PILEUP', 'scaleFactor_ELE', 'scaleFactor_MUON',
                                  'scaleFactor_LepTRIGGER'],
                                 library="ak", entry_stop=numevents):
            
            data['totalWeight'] = calc_weight(data, sample)
            data = apply_cuts(data)
            data['mllll'] = calc_mllll(data['lep_pt'], data['lep_eta'], data['lep_phi'], data['lep_E'])
            data_all.append(data)

    result = ak.concatenate(data_all)
    elapsed = time.time() - start
    print(f"\tProcessed {len(result)} events in {round(elapsed, 1)}s")
    return result

def calc_weight(data, sample):
    """Calculate event weights based on cross-section and other factors."""
    xsec_weight = get_xsec_weight(sample)
    return (xsec_weight * data.mcWeight * data.scaleFactor_PILEUP * data.scaleFactor_ELE *
            data.scaleFactor_MUON * data.scaleFactor_LepTRIGGER)

def get_xsec_weight(sample):
    """Retrieve cross-section weight from configuration."""
    info = infofile.infos[sample]
    lumi = 10  # Example luminosity in fb^-1
    return (lumi * 1000 * info["xsec"]) / (info["sumw"] * info["red_eff"])

def apply_cuts(data):
    """Apply physics-based cuts to the data."""
    charge_cut = (ak.sum(data['lep_charge'], axis=1) == 0)
    type_cut = ((ak.sum(data['lep_type'], axis=1) == 44) | 
                (ak.sum(data['lep_type'], axis=1) == 48) | 
                (ak.sum(data['lep_type'], axis=1) == 52))
    return data[charge_cut & type_cut]

def calc_mllll(lep_pt, lep_eta, lep_phi, lep_E):
    """Calculate the invariant mass of four leptons."""
    p4 = vector.zip({"pt": lep_pt, "eta": lep_eta, "phi": lep_phi, "E": lep_E})
    return (p4[:, 0] + p4[:, 1] + p4[:, 2] + p4[:, 3]).mass * MeV

def get_data_from_files():
    """Process all files and publish data to RabbitMQ."""
    data = {}
    print('Processing "Background $Z,t\bar{t}$" samples')
    frames = []
    for val in samples[r'Background $Z,t\bar{t}$']['list']:
        fileString = tuple_path + "MC/mc_" + str(infofile.infos[val]["DSID"]) + "." + val + ".4lep.root"
        temp = read_file(fileString, val)
        frames.append(temp)
    data[r'Background $Z,t\bar{t}$'] = ak.concatenate(frames)
    publish_data(data, "background_zt_data")  
    send_completion_message() 
    return data

if __name__ == "__main__":
    start = time.time()
    data = get_data_from_files()
    elapsed = time.time() - start
    print(f"Time taken: {round(elapsed, 1)}s")
