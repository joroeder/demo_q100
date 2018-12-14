"""oemof application for research project quarree100.

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

# Default logger of oemof
from oemof.tools import logger
from oemof.tools import economics
from oemof.tools import helpers
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging
import os
import pandas as pd
import pprint as pp
import matplotlib.pyplot as plt
import config as cfg

### Initialise the Energy System

logger.define_logging()
logging.info('Initialize the energy system')
number_timesteps = cfg.get('general_data', 'number_timesteps')
date_time_index = pd.date_range('1/1/2012',
                                periods=number_timesteps,
                                freq='H')
energysystem = solph.EnergySystem(timeindex=date_time_index)

# Read Data-file
path_to_data = os.path.join(os.path.expanduser("~"), cfg.get('paths', 'data'))
data = pd.read_csv(os.path.join(path_to_data,
                                'test-data_normiert.csv'), sep=";")

# Getting the interest rate used for all invest calculations
rate = cfg.get('general_data', 'interest_rate')

epc_storage_heat = economics.annuity(
    capex=cfg.get('fix_costs', 'storage_heat'),
    n=cfg.get('lifetime', 'storage_heat'),
    wacc=rate)*number_timesteps/8760
        
epc_storage_elec = economics.annuity(
    capex=cfg.get('fix_costs', 'storage_elec'),
    n=cfg.get('lifetime', 'storage_elec'),
    wacc=rate)*number_timesteps/8760

epc_storage_H2 = economics.annuity(
    capex=cfg.get('fix_costs', 'storage_H2'),
    n=cfg.get('lifetime', 'storage_H2'),
    wacc=rate)*number_timesteps/8760

epc_chp_gas = economics.annuity(
    capex=cfg.get('fix_costs', 'chp_gas'),
    n=cfg.get('lifetime', 'chp_gas'),
    wacc=rate)*number_timesteps/8760

epc_boiler_gas = economics.annuity(
    capex=cfg.get('fix_costs', 'boiler_gas'),
    n=cfg.get('lifetime', 'boiler_gas'),
    wacc=rate)*number_timesteps/8760

epc_heatpump_el = economics.annuity(
    capex=cfg.get('fix_costs', 'heatpump_el'),
    n=cfg.get('lifetime', 'heatpump_el'),
    wacc=rate)*number_timesteps/8760

epc_electrolysis_pem = economics.annuity(
    capex=cfg.get('fix_costs', 'electrolysis_pem'),
    n=cfg.get('lifetime', 'electrolysis_pem'),
    wacc=rate)*number_timesteps/8760

epc_chp_H2 = economics.annuity(
    capex=cfg.get('fix_costs', 'chp_H2'),
    n=cfg.get('lifetime', 'chp_H2'),
    wacc=rate)*number_timesteps/8760

        
logging.info('Create oemof objects')

## Defining the Buses
# create natural gas bus
bgas = solph.Bus(label='bgas')

# create electricity bus
bel = solph.Bus(label='bel')

# create electricity bus
beloff = solph.Bus(label='beloff')

# create heat bus (=district heatin net)
bheat = solph.Bus(label='bheat')

# create heat bus (=district heatin net)
bH2 = solph.Bus(label='bH2')

# add bgas and bel to energysystem
energysystem.add(bgas, bel, bheat, bH2, beloff)

# Defining and Adding Excess Sinks
energysystem.add(solph.Sink(label='excess_bel', inputs={bel: solph.Flow()}))

energysystem.add(solph.Sink(label='excess_beloff',
                           inputs={beloff: solph.Flow()}))

energysystem.add(solph.Sink(label='excess_bheat',
                            inputs={bheat: solph.Flow()}))

energysystem.add(solph.Sink(label='excess_bgas', inputs={bgas: solph.Flow()}))

energysystem.add(solph.Sink(label='excess_bH2', inputs={bH2: solph.Flow()}))


## Defining the Energy Sources

# create source object representing the natural gas commodity
energysystem.add(solph.Source(
    label='gas_resource',
    outputs={bgas: solph.Flow(
        variable_costs=cfg.get('prices_sources', 'price_gas'),
        emission=cfg.get('emissions_sources', 'CO2_gas'))}))

# create source object representing the electricity net
energysystem.add(solph.Source(
    label='elec_net',
    outputs={bel: solph.Flow(
        variable_costs=cfg.get('prices_sources', 'price_elec'),
        emission=cfg.get('emissions_sources', 'CO2_elec'))}))

# create source object representing the cut-off electricity
energysystem.add(solph.Source(
    label='elec_net_off',
    outputs={beloff: solph.Flow(
        actual_value=data['elec_off'], fixed=True,
        nominal_value=cfg.get('source_scaling', 'factor_elec_off'))}))

## Help - Transformer
energysystem.add(solph.Transformer(
    label='trans_beloff', inputs={beloff: solph.Flow()},
    outputs={bel: solph.Flow(
        nominal_value=None,
        variable_costs=cfg.get('prices_sources', 'price_elec_off'),
        emissions=cfg.get('emissions_sources', 'CO2_elec_off'))},
    conversion_factors={bel: 1}))

## DEMAND
# create simple sink object representing the electrical demand
energysystem.add(solph.Sink(
    label='demand_el', inputs={bel: solph.Flow(
        actual_value=data['demand_el'], fixed=True,
        nominal_value=cfg.get('demand_scaling', 'elec'))}))

# create simple sink object representing the heat demand
energysystem.add(solph.Sink(
    label='demand_heat',
    inputs={bheat: solph.Flow(
        actual_value=data['demand_heat'], fixed=True,
        nominal_value=cfg.get('demand_scaling', 'heat'))}))


## TRANSFORMERS

# create a simple transformer object representing a chp plant
energysystem.add(solph.Transformer(
    label='chp_gas',
    inputs={bgas: solph.Flow()},
    outputs={
        bel: solph.Flow(nominal_value=None,
                        investment=solph.Investment(ep_costs=epc_chp_gas)),
        bheat: solph.Flow(nominal_value=None)},
    conversion_factors={bel: cfg.get('conversion_factors', 'chp_gas_bel'),
                        bheat: cfg.get('conversion_factors',
                                       'chp_gas_bheat')}))

# create a simple transformer object representing a H2 chp
energysystem.add(solph.Transformer(
    label='chp_H2',
    inputs={bH2: solph.Flow()},
    outputs={
        bel: solph.Flow(nominal_value=None,
                        investment=solph.Investment(ep_costs=epc_chp_H2)),
        bheat: solph.Flow(nominal_value=None)},
    conversion_factors={bel: cfg.get('conversion_factors', 'chp_H2_bel'),
                        bheat: cfg.get('conversion_factors', 'chp_H2_bheat')}))

# create a simple transformer object representing a heater
energysystem.add(solph.Transformer(
    label='boiler_gas',
    inputs={bgas: solph.Flow()},
    outputs={
        bheat: solph.Flow(nominal_value=None, investment=solph.Investment(
                ep_costs=epc_boiler_gas))},
    conversion_factors={bheat: cfg.get('conversion_factors',
                                       'boiler_gas_bheat')}))

# create a simple transformer object representing a air heat pump
energysystem.add(solph.Transformer(
    label='heatpump_el',
    inputs={bel: solph.Flow()},
    outputs={
        bheat: solph.Flow(nominal_value=None, investment=solph.Investment(
                ep_costs=epc_heatpump_el))},
    conversion_factors={bheat: cfg.get('conversion_factors',
                                       'heatpump_el_bheat')}))

# power-to-gas
energysystem.add(solph.Transformer(
    label='electrolysis_pem',
    inputs={bel: solph.Flow()},
    outputs={
        bH2: solph.Flow(nominal_value=None, investment=solph.Investment(
                ep_costs=epc_electrolysis_pem)),
        bheat: solph.Flow(nominal_value=None)},
    conversion_factors={bH2: cfg.get('conversion_factors',
                                     'electrolysis_pem_bH2'),
                        bheat: cfg.get('conversion_factors',
                                       'electrolysis_pem_bheat')}))

# Storages
NAMES_Storages = [
    {'name': 'storage_elec', 'bus': bel, 'epc': epc_storage_elec},
    {'name': 'storage_heat', 'bus': bheat, 'epc': epc_storage_heat},
    {'name': 'storage_H2', 'bus': bH2, 'epc': epc_storage_H2}]

for data_set in NAMES_Storages:
    name = data_set['name']
    
    energysystem.add(solph.components.GenericStorage(
        label='{0}'.format(name),
        inputs={data_set['bus']: solph.Flow()},
        outputs={data_set['bus']: solph.Flow()},
        capacity_loss=cfg.get(name, 'capacity_loss'),
        initial_capacity=cfg.get(name, 'initial_capacity'),
        invest_relation_input_capacity=cfg.get(
            name, 'invest_relation_input_capacity'),
        invest_relation_output_capacity=cfg.get(
            name, 'invest_relation_output_capacity'),
        inflow_conversion_factor=cfg.get(name, 'inflow_conversion_factor'),
        outflow_conversion_factor=cfg.get(name, 'outflow_conversion_factor'),
        investment=solph.Investment(ep_costs=data_set['epc'])))


### Optimise the energy system

logging.info('Optimise the energy system')

# initialise the operational model
om = solph.Model(energysystem)

## Global CONSTRAINTS: CO2 Limit
solph.constraints.emission_limit(
    om, flows=None,
    limit=cfg.get('global_constraints', 'CO2_Limit'))

logging.info('Solve the optimization problem')
# if tee_switch is true solver messages will be displayed
om.solve(solver='cbc', solve_kwargs={'tee': False})

logging.info('Store the energy system with the results.')

# add results to the energy system to make it possible to store them.
energysystem.results['main'] = outputlib.processing.results(om)
energysystem.results['meta'] = outputlib.processing.meta_results(om)

# store energy system with results
energysystem.dump(dpath=None, filename=None)


### Check and plot the results

logging.info('Restore the energy system and the results.')
energysystem = solph.EnergySystem()
energysystem.restore(dpath=None, filename=None)

# define an alias for shorter calls below (optional)
results = energysystem.results['main']

# get all variables of a specific component/bus
electricity_bus = outputlib.views.node(results, 'bel')["sequences"]
gas_bus = outputlib.views.node(results, 'bgas')["sequences"]
heat_bus = outputlib.views.node(results, 'bheat')["sequences"]
H2_bus = outputlib.views.node(results, 'bH2')["sequences"]
Elec_off_bus = outputlib.views.node(results, 'beloff')["sequences"]

# Define dataframe to store and export all energyflows
df_ges = pd.concat([electricity_bus, gas_bus, heat_bus, H2_bus, Elec_off_bus],
                   axis=1)

# plot the time series (sequences) of a specific component/bus
if plt is not None:
    ax=electricity_bus.plot(kind='line', drawstyle='steps-post',
                            legend='right')
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0.)
    plt.show()
    
    Elec_off_bus.plot(kind='line', drawstyle='steps-post')
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0.)
    plt.show()
    
    gas_bus.plot(kind='line', drawstyle='steps-post')
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0.)
    plt.show()
    
    heat_bus.plot(kind='line', drawstyle='steps-post')
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0.)
    plt.show()
    
    H2_bus.plot(kind='line', drawstyle='steps-post')
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0.)
    plt.show()

# print the solver results
print('********* Meta results *********')
pp.pprint(energysystem.results['meta'])
print('')

# print the sums of the flows around the electricity bus
print('********* Main results *********')
print(electricity_bus.sum(axis=0))
print(Elec_off_bus.sum(axis=0))
print(gas_bus.sum(axis=0))
print(heat_bus.sum(axis=0))
print(H2_bus.sum(axis=0))
###

#getting the installed transformer capacities
p_chp_gas = outputlib.views.node(results, 'chp_gas')["scalars"][0]
p_chp_H2 = outputlib.views.node(results, 'chp_H2')["scalars"][0]
p_electrolysis_pem = outputlib.views.node(results,
                                          'electrolysis_pem')["scalars"][0]
p_boiler_gas = outputlib.views.node(results, 'boiler_gas')["scalars"][0]
p_heatpump_el = outputlib.views.node(results, 'heatpump_el')["scalars"][0]
y = [p_chp_gas, p_chp_H2, p_electrolysis_pem, p_boiler_gas, p_heatpump_el]
x = ['chp_gas', 'chp_H2', 'electrolysis', 'gas boiler', 'Heatpump']
width = 1/2
plt.bar(x, y, width, color="blue")
plt.ylabel('Installierte Leistung [kW]')
plt.show()

# storages capacities
c_storage_elec = outputlib.views.node(results, 'storage_elec')["scalars"][1]
c_storage_heat = outputlib.views.node(results, 'storage_heat')["scalars"][1]
c_storgae_H2 = outputlib.views.node(results, 'storage_H2')["scalars"][1]

plt.bar(['storage_elec', 'storage_heat', 'storage_H2'],
        [c_storage_elec, c_storage_heat, c_storgae_H2],
        width = 0.5, color="blue")
plt.ylabel('Kapazität [kWh]')
plt.show()

# the result_gesamt df is exported in excel
#with pd.ExcelWriter('Results.xlsx') as xls:
#    df_ges.to_excel(xls, sheet_name = 'Timeseries')
#    df_invest_ges.to_excel(xls, sheet_name = 'Invest')