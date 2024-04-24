# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 03:43:35 2024

@author: Mohammad
"""

import sys
import time
import json
import pika

import uproot
import awkward as ak
import vector
import numpy as np

import infofile 

# Constants
lumi = 10  # fb-1 for all data
fraction = 1.0  # Full dataset
tuple_path = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/4lep/"

samples = {
    'data': {
        'list': ['data_A', 'data_B', 'data_C', 'data_D'],
    },
    r'Background $Z,t\bar{t}$': {
        'list': ['Zee', 'Zmumu', 'ttbar_lep'],
        'color': "#6b59d3"  # purple
    },
    r'Background $ZZ^*$': {
        'list': ['llll'],
        'color': "#ff0000"  # red
    },
    r'Signal ($m_H$ = 125 GeV)': {
        'list': ['ggH125_ZZ4lep', 'VBFH125_ZZ4lep', 'WH125_ZZ4lep', 'ZH125_ZZ4lep'],
        'color': "#00cdff"  # light blue
    },
}

MeV = 0.001
GeV = 1.0

def get_xsec_weight(sample):
    info = infofile.infos[sample]
    xsec_weight = (lumi * 1000 * info["xsec"]) / (info["sumw"] * info["red_eff"])
    return xsec_weight

def calc_weight(xsec_weight, events):
    return (xsec_weight * events.mcWeight * events.scaleFactor_PILEUP *
            events.scaleFactor_ELE * events.scaleFactor_MUON * events.scaleFactor_LepTRIGGER)

def calc_mllll(lep_pt, lep_eta, lep_phi, lep_E):
    p4 = vector.zip({"pt": lep_pt, "eta": lep_eta, "phi": lep_phi, "E": lep_E})
    return (p4[:, 0] + p4[:, 1] + p4[:, 2] + p4[:, 3]).M * MeV

def cut_lep_charge(lep_charge):
    return lep_charge[:, 0] + lep_charge[:, 1] + lep_charge[:, 2] + lep_charge[:, 3] != 0

def cut_lep_type(lep_type):
    sum_lep_type = lep_type[:, 0] + lep_type[:, 1] + lep_type[:, 2] + lep_type[:, 3]
    return (sum_lep_type != 44) & (sum_lep_type != 48) & (sum_lep_type != 52)

def read_file(path, sample):
    start = time.time()
    data_all = []
    with uproot.open(path + ":mini") as tree:
        numevents = tree.num_entries
        if 'data' not in sample:
            xsec_weight = get_xsec_weight(sample)
        for data in tree.iterate(['lep_pt', 'lep_eta', 'lep_phi', 'lep_E', 'lep_charge', 'lep_type',
                                  'mcWeight', 'scaleFactor_PILEUP', 'scaleFactor_ELE', 'scaleFactor_MUON', 'scaleFactor_LepTRIGGER'],
                                 library="ak", entry_stop=int(numevents * fraction)):
            if 'data' not in sample:
                data['totalWeight'] = calc_weight(xsec_weight, data)
            data = data[~cut_lep_charge(data.lep_charge)]
            data = data[~cut_lep_type(data.lep_type)]
            data['mllll'] = calc_mllll(data.lep_pt, data.lep_eta, data.lep_phi, data.lep_E)
            data_all.append(data)
            elapsed = time.time() - start
            print(f"\t\t nIn: {len(data)}, nOut: {len(data)}, in {round(elapsed,1)}s")
    return ak.concatenate(data_all)

def get_data_from_files():
    data = {}
    for s in samples:
        print(f'Processing {s} samples')
        frames = []
        for val in samples[s]['list']:
            prefix = "Data/" if s == 'data' else f"MC/mc_{infofile.infos[val]['DSID']}."
            fileString = f"{tuple_path}{prefix}{val}.4lep.root"
            frames.append(read_file(fileString, val))
        data[s] = ak.concatenate(frames)
    return data

class AwkwardJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ak.Array):
            return ak.to_list(obj)  # Convert awkward arrays to lists
        return super().default(obj)

def publish_data(data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='plotting_queue')
    # Serialize data using the custom JSON encoder
    processed_data = json.dumps(data, cls=AwkwardJSONEncoder, indent=4)
    channel.basic_publish(exchange='', routing_key='plotting_queue', body=processed_data)
    connection.close()
    
if __name__ == "__main__":
    start = time.time()
    data = get_data_from_files()
    publish_data(data)
    elapsed = time.time() - start
    print(f"Time taken: {round(elapsed,1)}s")
