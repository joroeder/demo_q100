"""
oemof application for research project quarree100

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

import energy_system_model as esm
import oemof.solph as solph
import oemof.outputlib as outputlib
import pandas as pd
import config as cfg
import os
from matplotlib import pyplot as plt

# Optimize the energysystem
results = esm.q100_demo()

# Restore the energysystem (derzeit nicht verwendet)
energysystem = solph.EnergySystem()
energysystem.restore(dpath=None, filename=None)

# get all variables of a specific component/bus
electricity_bus = outputlib.views.node(results, 'bel')["sequences"]
gas_bus = outputlib.views.node(results, 'bgas')["sequences"]
heat_bus = outputlib.views.node(results, 'bheat')["sequences"]
H2_bus = outputlib.views.node(results, 'bH2')["sequences"]
Elec_off_bus = outputlib.views.node(results, 'beloff')["sequences"]

# Define dataframe to store and export specific energy-flows
df_ges = pd.concat([electricity_bus, gas_bus, heat_bus, H2_bus, Elec_off_bus],
                   axis=1)

# getting the installed transformer capacities
p_chp_gas = outputlib.views.node(results, 'chp_gas')["scalars"][0]
p_chp_H2 = outputlib.views.node(results, 'chp_H2')["scalars"][0]
p_electrolysis_pem = outputlib.views.node(
    results, 'electrolysis_pem')["scalars"][0]
p_boiler_gas = outputlib.views.node(results, 'boiler_gas')["scalars"][0]
p_heatpump_el = outputlib.views.node(results, 'heatpump_el')["scalars"][0]
c_storage_elec = outputlib.views.node(results, 'storage_elec')["scalars"][1]
c_storage_heat = outputlib.views.node(results, 'storage_heat')["scalars"][1]
c_storgae_H2 = outputlib.views.node(results, 'storage_H2')["scalars"][1]

df_invest_ges = pd.DataFrame([[
    p_chp_gas, p_chp_H2, p_electrolysis_pem, p_boiler_gas, p_heatpump_el,
    c_storage_elec, c_storage_heat, c_storgae_H2
    ]],
    columns=['p_chp_gas', 'p_chp_H2', 'p_electrolysis_pem',
             'p_boiler_gas', 'p_heatpump_el', 'c_storage_elec',
             'c_storage_heat', 'c_storgae_H2'])

# the result_gesamt df is exported in excel
path_to_results = os.path.join(os.path.expanduser("~"),
                               cfg.get('paths', 'results'))
filename = 'results.xlsx'
with pd.ExcelWriter(os.path.join(path_to_results, filename)) as xls:
    df_ges.to_excel(xls, sheet_name='Timeseries')
    df_invest_ges.to_excel(xls, sheet_name='Invest')

# plot the time series (sequences) of a specific component/bus
electricity_bus.plot(kind='line', drawstyle="steps-mid", subplots=False,
                     sharey=True)
gas_bus.plot(kind='line', drawstyle="steps-mid", subplots=False, sharey=True)
plt.show()

# plot the installed Transformer Capacities
y = [p_chp_gas, p_chp_H2, p_electrolysis_pem, p_boiler_gas, p_heatpump_el]
x = ['chp_gas', 'chp_H2', 'electrolysis', 'gas boiler', 'Heatpump']
width = 1/2
plt.bar(x, y, width, color="blue")
plt.ylabel('Installierte Leistung [kW]')
plt.show()

# plot the installed Storage Capacities
plt.bar(['storage_elec', 'storage_heat', 'storage_H2'],
        [c_storage_elec, c_storage_heat, c_storgae_H2],
        width = 0.5, color="blue")
plt.ylabel('Kapazität [kWh]')
plt.show()
