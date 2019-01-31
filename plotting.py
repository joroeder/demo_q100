"""
oemof application for research project quarree100.

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

import oemof.outputlib as outputlib
from matplotlib import pyplot as plt


def plot_buses(res=None, es=None):

    l_buses = []

    for n in es.nodes:
        type_name = str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Bus":
            l_buses.append(n.label)

    for n in l_buses:
        bus_sequences = outputlib.views.node(res, n)["sequences"]
        bus_sequences.plot(kind='line', drawstyle="steps-mid", subplots=False,
                           sharey=True)
        plt.show()


def plot_trans_invest(res=None, es=None):

    l_transformer = []

    for n in es.nodes:
        type_name = str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Transformer":
            l_transformer.append(n.label)

    p_trans_install = []

    for q in l_transformer:
        p_install = outputlib.views.node(res, q)["scalars"][0]
        p_trans_install.append(p_install)

    # plot the installed Transformer Capacities
    y = p_trans_install
    x = l_transformer
    width = 1/2
    plt.bar(x, y, width, color="blue")
    plt.ylabel('Installierte Leistung [kW]')
    plt.show()


def plot_storages_SoC(res=None, es=None):

    l_storages = []

    for n in es.nodes:
        type_name = str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "components.GenericStorage":
            l_storages.append(n.label)

    for n in l_storages:
        SoC_sequences = outputlib.views.node(res, n)["sequences"]
        SoC_sequences = SoC_sequences.drop(SoC_sequences.columns[[0, 2]], 1)
        SoC_sequences.plot(kind='line', drawstyle="steps-mid", subplots=False,
                           sharey=True)
        plt.show()


def plot_storages_invest(res=None, es=None):

    l_storages = []

    for n in es.nodes:
        type_name = str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "components.GenericStorage":
            l_storages.append(n.label)

    c_storage_install = []

    for n in l_storages:
        c_storage = outputlib.views.node(res, n)["scalars"][0]
        c_storage_install.append(c_storage)

    # plot the installed Storage Capacities
    plt.bar(l_storages, c_storage_install, width = 0.5, color="blue")
    plt.ylabel('Kapazität [kWh]')
    plt.show()