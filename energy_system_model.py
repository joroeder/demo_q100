"""
oemof application for research project quarree100.

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

# Default logger of oemof
from oemof.tools import logger
from oemof.tools import economics
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging
import os
import pandas as pd
import config as cfg


def q100_demo():

    # Initialise the Energy System
    logger.define_logging()
    logging.info('Initialize the energy system')
    number_timesteps = cfg.get('general_data', 'number_timesteps')
    date_time_index = pd.date_range('1/1/2012',
                                    periods=number_timesteps,
                                    freq='H')
    energysystem = solph.EnergySystem(timeindex=date_time_index)

    # Read Data-file
    path_to_data = os.path.join(os.path.expanduser("~"),
                                cfg.get('paths', 'data'))
    data = pd.read_csv(os.path.join(path_to_data,
                                    'test-data_normiert.csv'), sep=";")

    # Getting the interest rate used for all invest calculations
    rate = cfg.get('general_data', 'interest_rate')

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

    epc_chp_h2 = economics.annuity(
        capex=cfg.get('fix_costs', 'chp_H2'),
        n=cfg.get('lifetime', 'chp_H2'),
        wacc=rate)*number_timesteps/8760

    logging.info('Create oemof objects')

    # Defining the Buses
    # create natural gas bus
    bgas = solph.Bus(label='bgas')

    # create electricity bus
    bel = solph.Bus(label='bel')

    # create electricity bus
    beloff = solph.Bus(label='beloff')

    # create heat bus (=district heatin net)
    bheat = solph.Bus(label='bheat')

    # create heat bus (=district heatin net)
    bh2 = solph.Bus(label='bH2')

    # add bgas and bel to energysystem
    energysystem.add(bgas, bel, bheat, bh2, beloff)

    # Defining and Adding Excess Sinks
    energysystem.add(solph.Sink(label='excess_bel',
                                inputs={bel: solph.Flow()}))

    energysystem.add(solph.Sink(label='excess_beloff',
                                inputs={beloff: solph.Flow()}))

    energysystem.add(solph.Sink(label='excess_bheat',
                                inputs={bheat: solph.Flow()}))

    energysystem.add(solph.Sink(label='excess_bgas',
                                inputs={bgas: solph.Flow()}))

    energysystem.add(solph.Sink(label='excess_bH2',
                                inputs={bh2: solph.Flow()}))

    # Defining the Energy Sources
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

    # Help - Transformer
    energysystem.add(solph.Transformer(
        label='trans_beloff', inputs={beloff: solph.Flow()},
        outputs={bel: solph.Flow(
            nominal_value=None,
            variable_costs=cfg.get('prices_sources', 'price_elec_off'),
            emissions=cfg.get('emissions_sources', 'CO2_elec_off'))},
        conversion_factors={bel: 1}))

    # DEMAND
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

    # TRANSFORMERS
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
        inputs={bh2: solph.Flow()},
        outputs={
            bel: solph.Flow(nominal_value=None,
                            investment=solph.Investment(ep_costs=epc_chp_h2)),
            bheat: solph.Flow(nominal_value=None)},
        conversion_factors={bel: cfg.get('conversion_factors', 'chp_H2_bel'),
                            bheat: cfg.get('conversion_factors',
                                           'chp_H2_bheat')}))

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
            bh2: solph.Flow(nominal_value=None, investment=solph.Investment(
                    ep_costs=epc_electrolysis_pem)),
            bheat: solph.Flow(nominal_value=None)},
        conversion_factors={bh2: cfg.get('conversion_factors',
                                         'electrolysis_pem_bH2'),
                            bheat: cfg.get('conversion_factors',
                                           'electrolysis_pem_bheat')}))

    # Read Storage Data
    df_storages_data = pd.read_excel(os.path.join(
            os.path.expanduser("~"), path_to_data, 'Parameter.xlsx'),
        sheet_name='Storages')

    # Convert Storage Data to Dict
    storages = df_storages_data.set_index('name').T.to_dict('dict')

    # Generate Storages from Storage Dict
    for storage in storages:

        epc_storage = economics.annuity(
            capex=storages[storage]['capex'],
            n=storages[storage]['n'],
            wacc=rate)*number_timesteps/8760

        energysystem.add(solph.components.GenericStorage(
            label=storage,
            inputs={eval(storages[storage]['bus']): solph.Flow()},
            outputs={eval(storages[storage]['bus']): solph.Flow()},
            capacity_loss=storages[storage]['capacity_loss'],
            invest_relation_input_capacity=storages[
                storage]['invest_relation_input_capacity'],
            invest_relation_output_capacity=storages[
                storage]['invest_relation_output_capacity'],
            inflow_conversion_factor=storages[
                storage]['inflow_conversion_factor'],
            outflow_conversion_factor=storages[storage][
                'outflow_conversion_factor'],
            investment=solph.Investment(ep_costs=epc_storage)))

    # Optimise the energy system
    logging.info('Optimise the energy system')

    # initialise the operational model
    om = solph.Model(energysystem)

    # Global CONSTRAINTS: CO2 Limit
    solph.constraints.emission_limit(
        om, flows=None, limit=cfg.get('global_constraints', 'CO2_Limit'))

    logging.info('Solve the optimization problem')
    # if tee_switch is true solver messages will be displayed
    om.solve(solver='cbc', solve_kwargs={'tee': False})

    logging.info('Store the energy system with the results.')

    # add results to the energy system to make it possible to store them.
    energysystem.results['main'] = outputlib.processing.results(om)
    # energysystem.results['meta'] = outputlib.processing.meta_results(om)

    # Store energy system with results
    # energysystem.dump(dpath=None, filename=None)

    # define an alias for shorter calls below (optional)
    results = energysystem.results['main']

    return results
