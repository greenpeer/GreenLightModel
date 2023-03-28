#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 21/03/2023
# @Author  : Daidai Qiu
# @Github  : https://github.com/greenpeer
# @Software: PyCharm
# @File    : gl_model.py

import math
import os
import re
import datetime
import numpy as np
import matlab.engine
import json
from sympy import symbols, pi
from sympy.parsing.sympy_parser import parse_expr
from scipy.integrate import solve_ivp


class GreenLightModel:
    """
    The GreenLight class represents a wrapper for the GreenLight MATLAB model. This class is used to run the GreenLight
    model, save the output, and perform various calculations with the obtained results.


    Attributes:
        p: A dictionary containing various parameters related to greenhouse systems.
        current_folder (str): The folder containing the class source file.
        output_folder (str): The folder where the output files will be saved.
        eng (MATLABEngine): A reference to the MATLAB engine instance.

    Methods:
        add_paths(): Adds required paths to MATLAB's search path.
        update_params(param_dict):Update the values of parameters in the given dictionary, overwriting the default values.
        run_green_light(lamp_type=None, weather=None, filename=None, param_names=None, param_vals=None, is_mature=False): Runs the GreenLight model with the given parameters,returns an instance of the GreenLight model with the completed simulation. Data of this simulation is given in 5-minute intervals.
        calculate_energy_consumption(gl, *array_keys): Calculate the energy consumption for the given parameters.
        quit(): Stop the MATLAB engine.
        makeArtificialInput: Make an artificial dataset to use as input for a GreenLight instance.
        co2ppm2dens: Convert CO2 molar concentration [ppm] to density [kg m^{-3}].
        day_light_sum: Calculate the light sum from the sun [MJ m^{-2} day^{-1}] for each day. These values will be constant for each day, and change at midnight.
        generate_datenum_list: Generates a list of MATLAB format datenums starting from the specified start_datenum and with the specified time interval and number of days.
        params_from_string(): Extracts all the parameters (i.e., variables) from the given formula string.
        formula_result(): Calculate the dependent parameters for the GreenLight model using the given formula string and parameters.
        default_output_folder(): Returns the default output folder path for the GreenLight model.
        data_folder(): Returns the data folder path for the GreenLight model.
        save_to_json(json_data, filename=None): Saves the data to a JSON file.
        print_all_dicts(): Prints all parameters in the dictionaries along with their keys, values, and comments.
        find_comment(var_name): Finds and returns the comment associated with a variable in the source code.
        help(): Prints the help text (docstring) describing the class and its dictionaries.
    """

    def __init__(self, output_folder=None):

        """Initializes an instance of the GreenLightModel class with default or user-specified parameters."""

        self.p = {
            "psi": 22,  # Mean greenhouse cover slope
            "aFlr": 4e4,  # Floor area [m^{2}]
            "aCov": 4.84e4,  # Surface of the cover including side walls [m^{2}]
            # Height of the main compartment [m] (the ridge height is 6.5, screen is 20 cm below it)
            "hAir": 6.3,
            "hGh": 6.905,  # Mean height of the greenhouse [m]
            "aRoof": 0.1169 * 4e4,  # Maximum roof ventilation area
            "hVent": 1.3,  # Vertical dimension of single ventilation opening [m]
            "cDgh": 0.75,  # Ventilation discharge coefficient [-]
            "lPipe": 1.25,  # Length of pipe rail system [m m^{-2}]
            "phiExtCo2": 7.2e4 * 4e4
            # Capacity of CO2 injection for the entire greenhouse [mg s^{-1}]
            / 1.4e4,
            "boiler": 300,  # Capacity of boiler [W]
            "pBoil": "boiler * aFlr",  # Capacity of boiler for the entire greenhouse [W]
            "hElevation": 100,  # Altitude of greenhouse m above sea level
            "co2SpDay": 1000,  # CO2 setpoint during the light period [ppm]
            "tSpNight": 18.5,  # temperature set point dark period [°C]
            "tSpDay": 19.5,  # temperature set point light period [°C]
            "rhMax": 87,  # maximum relative humidity [ %]
            # P-band for ventilation due to high temperature [°C]
            "ventHeatPband": 4,
            # P-band for ventilation due to high relative humidity [ % humidity]
            "ventRhPband": 50,
            # P-band for screen opening due to high relative humidity [ % humidity]
            "thScrRhPband": 10,
            "lampsOn": 0,  # time of day (in morning) to switch on lamps [h]
            "lampsOff": 12,  # time of day (in evening) to switch off lamps 	[h]
            # lamps are switched off if global radiation is above this value [W m^{-2}]
            "lampsOffSun": 400,
            # Predicted daily radiation sum from the sun where lamps are not used that day [MJ m^{-2} day^{-1}]
            "lampRadSumLimit": 10,
            "capGroPipe": "0.25*pi*lPipe*((phiPipeE**2-phiPipeI**2)*rhoSteel*cPSteel+phiPipeI**2*rhoWater*cPWater)",
            # "aGroPipe": "pi * lGroPipe * phiGroPipeE",
        }
        self.general_parameters = {
            "alfaLeafAir": 5,  # Convective heat exchange coefficient from the canopy leaf to the greenhouse air W m^{-2} K^{-1}
            "L": 2.45e6,  # Latent heat of evaporation J kg^{-1}{water}
            "sigma": 5.67e-8,  # Stefan-Boltzmann constant W m^{-2} K^{-4}
            "epsCan": 1,  # FIR emission coefficient of canopy -
            "epsSky": 1,  # FIR emission coefficient of the sky -
            "etaGlobNir": 0.5,  # Ratio of NIR in global radiation -
            "etaGlobPar": 0.5,  # Ratio of PAR in global radiation -
            "etaMgPpm": 0.554,  # CO2 conversion factor from mg m^{-3} to ppm ppm mg^{-1} m^{3}
            "etaRoofThr": 0.9,  # Ratio between roof vent area and total vent area where no chimney effects is assumed -
            "rhoAir0": 1.2,  # Density of air at sea level kg m^{-3}
            "rhoCanPar": 0.07,  # PAR reflection coefficient -
            "rhoCanNir": 0.35,  # NIR reflection coefficient of the top of the canopy -
            "rhoSteel": 7850,  # Density of steel kg m^{-3}
            "rhoWater": 1e3,  # Density of water kg m^{-3}
            "gamma": 65.8,  # Psychrometric constant Pa K^{-1}
            "omega": 1.99e-7,  # Yearly frequency to calculate soil temperature s^{-1}
            "capLeaf": 1.2e3,  # Heat capacity of canopy leaves J K^{-1} m^{-2}{leaf}
            "cEvap1": 4.3,  # Coefficient for radiation effect on stomatal resistance W m^{-2}
            "cEvap2": 0.54,  # Coefficient for radiation effect on stomatal resistance W m^{-2}
            "cEvap3Day": 6.1e-7,  # Coefficient for co2 effect on stomatal resistance (day) ppm^{-2}
            "cEvap3Night": 1.1e-11,  # Coefficient for co2 effect on stomatal resistance (night) ppm^{-2}
            "cEvap4Day": 4.3e-6,  # Coefficient for vapor pressure effect on stomatal resistance (day) Pa^{-2}
            "cEvap4Night": 5.2e-6,  # Coefficient for vapor pressure effect on stomatal resistance (night) Pa^{-2}
            "cPAir": 1e3,  # Specific heat capacity of air J K^{-1} kg^{-1}
            "cPSteel": 0.64e3,  # Specific heat capacity of steel J K^{-1} kg^{-1}
            "cPWater": 4.18e3,  # Specific heat capacity of water J K^{-1} kg^{-1}
            "g": 9.81,  # Acceleration of gravity m s^{-2}
            "hSo1": 0.04,  # Thickness of soil layer 1 m
            "hSo2": 0.08,  # Thickness of soil layer 2 m
            "hSo3": 0.16,  # Thickness of soil layer 3 m
            "hSo4": 0.32,  # Thickness of soil layer 4 m
            "hSo5": 0.64,  # Thickness of soil layer 5 m
            "k1Par": 0.7,  # PAR extinction coefficient of the canopy -
            "k2Par": 0.7,  # PAR extinction coefficient of the canopy for light reflected from the floor -
            "kNir": 0.27,  # NIR extinction coefficient of the canopy -
            "kFir": 0.94,  # FIR extinction coefficient of the canopy -
            "mAir": 28.96,  # Molar mass of air kg kmol^{-1}
            "hSoOut": 1.28,  # Thickness of the external soil layer m
            "mWater": 18,  # Molar mass of water kg kmol^{-1}
            "R": 8314,  # Molar gas constant J kmol^{-1} K^{-1}
            "rCanSp": 5,  # Radiation value above the canopy when night becomes day W m^{-2}
            "rB": 275,  # Boundary layer resistance of the canopy for transpiration s m^{-1}
            "rSMin": 82,  # Minimum canopy resistance for transpiration s m^{-1}
            "sRs": -1,  # Slope of smoothed stomatal resistance model m W^{-2}
            "sMV12": -0.1,  # Slope of smoothed condensation model Pa^{-1}
        }
        self.construction_parameters = {
            # Greenhouse Construction properties
            "etaGlobAir": 0.1,  # Ratio of global radiation absorbed by the greenhouse construction
            "psi": 22,  # Mean greenhouse cover slope
            "aFlr": 1.4e4,  # Floor area of greenhouse [m^{2}]
            "aCov": 1.8e4,  # Surface of the cover including side walls [m^{2}]
            "hAir": 3.8,  # Height of the main compartment [m]
            "hGh": 4.2,  # Mean height of the greenhouse [m]
            "cHecIn": 1.86,  # Convective heat exchange between cover and outdoor air W m^{-2} K^{-1}
            "cHecOut1": 2.8,  # Convective heat exchange parameter between cover and outdoor air W m^{-2}{cover} K^{-1}
            "cHecOut2": 1.2,  # Convective heat exchange parameter between cover and outdoor air J m^{-3} K^{-1}
            "cHecOut3": 1,  # Convective heat exchange parameter between cover and outdoor air -
            "hElevation": 0,  # Altitude of greenhouse m above sea level
        }
        self.ventilation_parameters = {
            # Ventilation properties
            "aRoof": 0.1169 * 4e4,  # Maximum roof ventilation area -
            "hVent": 0.68,  # Vertical dimension of single ventilation opening [m]
            "etaInsScr": 1,  # Porosity of the insect screen -
            "aSide": 0,  # Side ventilation area -
            "cDgh": 0.75,  # Ventilation discharge coefficient -
            "cLeakage": 1e-4,  # Greenhouse leakage coefficient -
            "cWgh": 0.09,  # Ventilation global wind pressure coefficient -
            "hSideRoof": 0,  # Vertical distance between mid points of side wall and roof ventilation opening m
        }
        self.roof_parameters = {
            # Roof
            "epsRfFir": 0.85,  # FIR emission coefficient of the roof -
            "rhoRf": 2.6e3,  # Density of the roof layer kg m^{-3}
            "rhoRfNir": 0.13,  # NIR reflection coefficient of the roof -
            "rhoRfPar": 0.13,  # PAR reflection coefficient of the roof -
            "rhoRfFir": 0.15,  # FIR reflection coefficient of the roof -
            "tauRfNir": 0.85,  # NIR transmission coefficient of the roof -
            "tauRfPar": 0.85,  # PAR transmission coefficient of the roof -
            "tauRfFir": 0,  # FIR transmission coefficient of the roof -
            "lambdaRf": 1.05,  # Thermal heat conductivity of the roof W m^{-1} K^{-1}
            "cPRf": 0.84e3,  # Specific heat capacity of roof layer J K^{-1} kg^{-1}
            "hRf": 4e-3,  # Thickness of roof layer m
        }
        self.whitewash_parameters = {
            # Whitewash
            "epsShScrPerFir": 0,  # FIR emission coefficient of the whitewash -
            "rhoShScrPer": 0,  # Density of the whitewash -
            "rhoShScrPerNir": 0,  # NIR reflection coefficient of whitewash -
            "rhoShScrPerPar": 0,  # PAR reflection coefficient of whitewash -
            "rhoShScrPerFir": 0,  # FIR reflection coefficient of whitewash -
            "tauShScrPerNir": 1,  # NIR transmission coefficient of whitewash -
            "tauShScrPerPar": 1,  # PAR transmission coefficient of whitewash -
            "tauShScrPerFir": 1,  # FIR transmission coefficient of whitewash -
            "lambdaShScrPer": float(
                "inf"
            ),  # Thermal heat conductivity of the whitewash W m^{-1} K^{-1}
            "cPShScrPer": 0,  # Specific heat capacity of the whitewash J K^{-1} kg^{-1}
            "hShScrPer": 0,  # Thickness of the whitewash m
        }
        self.shadow_screen_parameters = {
            # Shadow screen
            "rhoShScrNir": 0,  # NIR reflection coefficient of shadow screen -
            "rhoShScrPar": 0,  # PAR reflection coefficient of shadow screen -
            "rhoShScrFir": 0,  # FIR reflection coefficient of shadow screen -
            "tauShScrNir": 1,  # NIR transmission coefficient of shadow screen -
            "tauShScrPar": 1,  # PAR transmission coefficient of shadow screen -
            "tauShScrFir": 1,  # FIR transmission coefficient of shadow screen -
            "etaShScrCd": 0,  # Effect of shadow screen on discharge coefficient -
            "etaShScrCw": 0,  # Effect of shadow screen on wind pressure coefficient -
            "kShScr": 0,  # Shadow screen flux coefficient m^{3} m^{-2} K^{-2/3} s^{-1}
        }
        self.thermal_screen_parameters = {
            # Thermal screen
            "epsThScrFir": 0.67,  # FIR emissions coefficient of the thermal screen -
            "rhoThScr": 0.2e3,  # Density of thermal screen kg m^{-3}
            "rhoThScrNir": 0.35,  # NIR reflection coefficient of thermal screen -
            "rhoThScrPar": 0.35,  # PAR reflection coefficient of thermal screen -
            "rhoThScrFir": 0.18,  # FIR reflection coefficient of thermal screen -
            "tauThScrNir": 0.6,  # NIR transmission coefficient of thermal screen -
            "tauThScrPar": 0.6,  # PAR transmission coefficient of thermal screen -
            "tauThScrFir": 0.15,  # FIR transmission coefficient of thermal screen -
            "cPThScr": 1.8e3,  # Specific heat capacity of thermal screen J kg^{-1} K^{-1}
            "hThScr": 0.35e-3,  # Thickness of thermal screen m
            "kThScr": 0.05e-3,  # Thermal screen flux coefficient m^{3} m^{-2} K^{-2/3} s^{-1}
        }
        self.blackout_screen_parameters = {
            # Blackout screen
            "epsBlScrFir": 0.67,  # FIR emissions coefficient of the blackout screen -
            "rhoBlScr": 0.2e3,  # Density of blackout screen kg m^{-3}
            "rhoBlScrNir": 0.35,  # NIR reflection coefficient of blackout screen -
            "rhoBlScrPar": 0.35,  # PAR reflection coefficient of blackout screen -
            "tauBlScrNir": 0.01,  # NIR transmission coefficient of blackout screen -
            "tauBlScrPar": 0.01,  # PAR transmission coefficient of blackout screen -
            "tauBlScrFir": 0.7,  # FIR transmission coefficient of blackout screen -
            "cPBlScr": 1.8e3,  # Specific heat capacity of blackout screen J kg^{-1} K^{-1}
            "hBlScr": 0.35e-3,  # Thickness of blackout screen m
            "kBlScr": 0.05e-3,  # Blackout screen flux coefficient m^{3} m^{-2} K^{-2/3} s^{-1}
        }
        self.floor_parameters = {
            # Floor
            "epsFlr": 1,  # FIR emission coefficient of the floor -
            "rhoFlr": 2300,  # Density of the floor kg m^{-3}
            "rhoFlrNir": 0.5,  # NIR reflection coefficient of the floor -
            "rhoFlrPar": 0.65,  # PAR reflection coefficient of the floor -
        }
        self.soil_parameters = {
            # Soil
            "rhoCpSo": 1.73e6,  # Volumetric heat capacity of the soil J m^{-3} K^{-1}
            "lambdaSo": 0.85,  # Thermal heat conductivity of the soil layers W m^{-1} K^{-1}
        }
        self.heating_system_parameters = {
            # Heating system
            "epsPipe": 0.88,  # FIR emission coefficient of the heating pipes -
            "phiPipeE": 51e-3,  # External diameter of pipes m
            "phiPipeI": 47e-3,  # Internal diameter of pipes m
            "lPipe": 1.875,  # Length of heating pipes per gh floor area m m^{-2}
            "boiler": 130,  # Capacity of boiler [W]
        }
        self.active_climate_control_parameters = {
            #  Active climate control
            "phiExtCo2": 7.2e4
            * 4e4
            / 1.4e4,  # Capacity of CO2 injection for the entire greenhouse [mg s^{-1}]
        }
        self.dependant_parameters = {
            # Other parameters that depend on previously defined parameters
            "capPipe": "0.25 * pi  * lPipe * ( (phiPipeE**2 - phiPipeI**2) * rhoSteel * cPSteel + phiPipeI**2 * rhoWater * cPWater )",  # Heat capacity of heating pipes [J K^{-1} m^{-2}]
            "rhoAir": "rhoAir0 * exp( g * mAir * hElevation / (293.15 * R))",  # Density of the air [kg m^{-3}]
            # Heat capacity of greenhouse objects [J K^{-1} m^{-2}]
            "capAir": "hAir*rhoAir*cPAir",  # air in main compartment
            "capFlr": "hFlr*rhoFlr*cPFlr",  # floor
            "capSo1": "hSo1*rhoCpSo",  # soil layer 1
            "capSo2": "hSo2*rhoCpSo",  # soil layer 2
            "capSo3": "hSo3*rhoCpSo",  # soil layer 3
            "capSo4": "hSo4*rhoCpSo",  # soil layer 4
            "capSo5": "hSo5*rhoCpSo",  # soil layer 5
            "capThScr": "hThScr*rhoThScr*cPThScr",  # thermal screen
            "capTop": "(hGh-hAir)*rhoAir*cPAir",  # air in top compartments
            "capBlScr": "hBlScr*rhoBlScr*cPBlScr",  # blackout screen
            "capCo2Air": "hAir",  # Capacity for CO2 [m]
            "capCo2Top": "hGh-hAir",  #  Capacity for CO2 [m]
            "aPipe": "pi*lPipe*phiPipeE",  # Surface of pipes for floor area [-]
            "fCanFlr": "1-0.49*pi*lPipe*phiPipeE",  # View factor from canopy to floor
            "pressure": "101325*(1-2.5577e-5*hElevation)**5.25588",  # Absolute air pressure at given elevation [Pa]
        }
        self.canopy_photosynthesis_parameters = {
            # Canopy photosynthesis
            "globJtoUmol": 2.3,  # Conversion factor from global radiation to PAR (etaGlobPar in [2], but that name has another meaning in [1]) umol{photons} J^{-1} 2.3 [2]
            "j25LeafMax": 210,  # Maximal rate of electron transport at 25°C of the leaf umol{e-} m^{-2}{leaf} s^{-1}
            "cGamma": 1.7,  # Effect of canopy temperature on CO2 compensation point umol{co2} mol^{-1}{air} K^{-1}
            "etaCo2AirStom": 0.67,  # Conversion from greenhouse air co2 concentration and stomatal co2 concentration umol{co2} mol^{-1}{air}
            "eJ": 37e3,  # Activation energy for Jpot calcualtion J mol^{-1}
            "t25k": 298.15,  # Reference temperature for Jpot calculation K
            "S": 710,  # Enthropy term for Jpot calculation J mol^{-1} K^{-1}
            "H": 22e4,  # Deactivation energy for Jpot calculation J mol^{-1}
            "theta": 0.7,  # Degree of curvature of the electron transport rate -
            "alpha": 0.385,  # Conversion factor from photons to electrons including efficiency term umol{e-} umol^{-1}{photons}
            "mCh2o": 30e-3,  # Molar mass of CH2O mg umol^{-1}
            "mCo2": 44e-3,  # Molar mass of CO2 mg umol^{-1}
            "parJtoUmolSun": 4.6,  # Conversion factor of sun's PAR from J to umol{photons} J^{-1}
            "laiMax": 3,  # leaf area index (m^{2}{leaf} m^{-2}{floor})
            "sla": 2.66e-5,  # specific leaf area (m^{2}{leaf} mg^{-1}{leaf}
            "rgr": 3e-6,  # relative growth rate {kg{dw grown} kg^{-1}{existing dw} s^{-1}} Assumed
            "cFruitMax": 300e3,  # maximum fruit size mg{fruit} m^{-2}
            "cFruitG": 0.27,  # Fruit growth respiration coefficient -
            "cLeafG": 0.28,  # Leaf growth respiration coefficient -
            "cStemG": 0.3,  # Stem growth respiration coefficient -
            "cRgr": 2.85e6,  # Regression coefficient in maintenance respiration function s^{-1}
            "q10m": 2,  # Q10 value of temperature effect on maintenance respiration -
            "cFruitM": 1.16e-7,  # Fruit maintenance respiration coefficient mg mg^{-1} s^{-1}
            "cLeafM": 3.47e-7,  # Leaf maintenance respiration coefficient mg mg^{-1} s^{-1}
            "cStemM": 1.47e-7,  # Stem maintenance respiration coefficient mg mg^{-1} s^{-1}
            "rgFruit": 0.328,  # Potential fruit growth coefficient mg m^{-2} s^{-1}
            "rgLeaf": 0.095,  # Potential leaf growth coefficient mg m^{-2} s^{-1}
            "rgStem": 0.074,  # Potential stem growth coefficient mg m^{-2} s^{-1}
        }
        self.carbohydrates_buffer_parameters = {
            # Carbohydrates buffer
            "cBufMax": 20e3,  # Maximum capacity of carbohydrate buffer mg m^{-2}
            "cBufMin": 1e3,  # Minimum capacity of carbohydrate buffer mg m^{-2}
            "tCan24Max": 24.5,  # Inhibition of carbohydrate flow because of high temperatures °C
            "tCan24Min": 15,  # Inhibition of carbohydrate flow because of low temperatures °C
            "tCanMax": 34,  # Inhibition of carbohydrate flow because of high instantenous temperatures °C
            "tCanMin": 10,  # Inhibition of carbohydrate flow because of low instantenous temperatures °C
        }
        self.crop_development_parameters = {
            # Crop development
            "tEndSum": 1035,  # Temperature sum where crop is fully generative °C day
        }
        self.control_parameters = {
            # Control parameters
            "rhMax": 90,  # upper bound on relative humidity [%]
            "dayThresh": 20,  # threshold to consider switch from night to day [W m^{-2}]
            "tSpDay": 19.5,  # Heat is on below this point in day [°C]
            "tSpNight": 16.5,  # Heat is on below this point in night [°C]
            "tHeatBand": -1,  # P-band for heating [°C]
            "tVentOff": 1,  # distance from heating setpoint where ventilation stops (even if humidity is too high) [°C]
            "tScreenOn": 2,  # distance from screen setpoint where screen is on (even if humidity is too high) [°C]
            "thScrSpDay": 5,  # Screen is closed at day when outdoor is below this temperature [°C]
            "thScrSpNight": 10,  # Screen is closed at night when outdoor is below this temperature [°C]
            "thScrPband": -1,  # P-band for thermal screen [°C]
            "co2SpDay": 800,  # Co2 is supplied if co2 is below this point during day [ppm]
            "co2Band": -100,  # P-band for co2 supply [ppm]
            "heatDeadZone": 5,  # zone between heating setpoint and ventilation setpoint [°C]
            "ventHeatPband": 4,  # P-band for ventilation due to excess heat [°C]
            "ventColdPband": -1,  # P-band for ventilation due to low indoor temperature [°C]
            "ventRhPband": 5,  # P-band for ventilation due to relative humidity [%]
            "thScrRh": -2,  # Relative humidity where thermal screen is forced to open, with respect to rhMax [%]
            "thScrRhPband": 2,  # P-band for thermal screen opening due to excess relative humidity [%]
            "thScrDeadZone": 4,  # Zone between heating setpoint and point where screen opens
            "lampsOn": 0,  # time of day to switch on lamps [hours since midnight]
            "lampsOff": 0,  # time of day to switch off lamps [hours since midnight]
            "dayLampStart": -1,  # Day of year when lamps start [day of year]
            "dayLampStop": 400,  # Day of year when lamps stop [day of year]
            "lampsOffSun": 400,  # lamps are switched off if global radiation is above this value [W m^{-2}]
            "lampRadSumLimit": 10,  # Predicted daily radiation sum from the sun where lamps are not used that day [MJ m^{-2} day^{-1}]
            "lampExtraHeat": 2,  # Control for lamps due to too much heat - switched off if indoor temperature is above setpoint+heatDeadZone+lampExtraHeat [°C] 2 [Chapter 5 Section 2.4 [9]]
            "blScrExtraRh": 100,  # Control for blackout screen due to humidity - screens open if relative humidity exceeds rhMax+blScrExtraRh [%] 100 (no blackout screen), 3 (with blackout screen) [Chapter 5 Section 2.4 [9]]
            "useBlScr": 0,  # Determines whether a blackout screen is used (1 if used, 0 otherwise) [-]
            "mechCoolPband": 1,  # P-band for mechanical cooling [°C]
            "mechDehumidPband": 2,  # P-band for mechanical dehumidification [%]
            "heatBufPband": -1,  # P-band for heating from the buffer [°C]
            "mechCoolDeadZone": 2,  # zone between heating setpoint and mechanical cooling setpoint [°C]
        }
        self.growpipe_parameters = {
            # Grow pipe parameters
            "epsGroPipe": 0,  # Emissivity of grow pipes [-]
            "lGroPipe": 1.655,  # Length of grow pipes per gh floor area m m^{-2}
            "phiGroPipeE": 35e-3,  # External diameter of grow pipes m
            "phiGroPipeI": (35e-3) - (1.2e-3),  # Internal diameter of grow pipes m
            "pBoilGro": 0,  # Capacity of the grow pipe heating system W
            "capGroPipe": "0.25*pi*lPipe*((phiPipeE^2-phiPipeI^2)*rhoSteel*cPSteel+phiPipeI^2*rhoWater*cPWater)",  # Heat capacity of grow pipes [J K^{-1} m^{-2}]
        }
        self.other_parameters = {
            # other parameters
            "cLeakTop": 0.5,  # Fraction of leakage ventilation going from the top [-]
            "minWind": 0.25,  # wind speed where the effect of wind on leakage begins [m s^{-1}]
        }

        # Get the current file and folder paths
        self.current_file = os.path.abspath(__file__)
        self.current_folder = os.path.dirname(self.current_file)

        # Set output folder path for the GreenLight model
        self.output_folder = (
            output_folder if output_folder else self.default_output_folder()
        )

        # If the output folder does not exist, create it
        if not os.path.exists(self.output_folder):
            os.makedirs(folder_name)

        # Starts the MATLAB engine
        self.eng = matlab.engine.start_matlab()

        # Add required paths to MATLAB's search path
        self.add_paths()

    def add_paths(self, *args):
        """
        Add additional required paths to MATLAB's search path.

        Returns:
            None

        """
        # Default folders to add to the search path
        folders = ["GreenLight", "DyMoMa", "GreenLight_Extensions"]
        folders += args
        for folder in folders:
            self.eng.addpath(
                self.eng.genpath(os.path.join(self.current_folder, folder))
            )

    def run_green_light(
        self,
        filename="",
        weatherInput="bei",
        seasonLength=1 / 24 / 6,
        firstDay=1,
        isMature=True,
        lampType="led",
    ):

        # Update the model parameters
        self.update_params(self.p)

        # Get parameter names and values as separate lists
        paramNames, paramVals = zip(*self.p.items())

        # Load the EnergyPlus data for the specified weather input, season length, and start day
        weather = self.eng.cutEnergyPlusData(
            firstDay,
            seasonLength,
            os.path.join(self.data_folder(), weatherInput + "EnergyPlus.mat"),
        )

        # Convert the loaded data to double precision
        weather = np.array(weather, dtype=np.float64)

        # Set default tolerance values
        abs_tol = 1e-6
        rel_tol = 1e-3

        # Set default weather value to 5 if not provided
        if weather is None:
            # Create artificial weather input with default value
            weather = self.eng.makeArtificialInput(5, nargout=1)

        # Set the lamp type to lowercase, default to "none" if not "hps" or "led"
        lamp_type = lampType.lower() if lampType else "none"

        # Set the filename for saving the output file, if specified
        filename = os.path.join(self.output_folder, filename) if filename else None

        # Determine if the output should be saved to a file
        save_file = bool(filename)

        # Set the elevation value based on the length of the first row of weather data
        elevation = weather[0][9] if len(weather[0]) >= 10 else 0

        # Print current date and time
        print(datetime.datetime.now())

        # Print starting information for the run_green_light method
        print(
            f"starting run_green_light. Lamp type: {lamp_type}. Filename: {filename}.json"
        )

        # Get weather datenum
        weather_datenum = weather[0, 0]

        # Convert the datenum value to a Python datetime object
        start_time = (
            datetime.datetime.fromordinal(int(weather_datenum))
            - datetime.timedelta(days=366)
            + datetime.timedelta(seconds=round((weather_datenum % 1) * 86400))
        )

        # Format the start_time as '01-Jan-2005 01:00:00'
        start_time = start_time.strftime("%d-%b-%Y %H:%M:%S")

        # Convert weather datenum to seconds from start time
        weather[:, 0] = (weather[:, 0] - weather[0, 0]) * 86400

        # Create GreenLightModel object with specified parameters
        gl = self.eng.createGreenLightModel(lamp_type, weather, start_time)

        # Set parameters for the GreenLight model
        self.eng.setParams4haWorldComparison(gl, nargout=0)

        # Set the elevation parameter
        self.eng.setParam(gl, "hElevation", elevation, nargout=0)

        # Set additional parameters, if provided
        for k in range(len(paramNames)):
            self.eng.setParam(gl, paramNames[k], paramVals[k], nargout=0)

        # Set dependent parameters
        self.eng.setDepParams(gl, nargout=0)

        # Set initial state values if the crop is mature
        if isMature:
            self.eng.setXParam(gl, "cFruit", 2.8e5, nargout=0)
            self.eng.setXParam(gl, "cLeaf", 0.9e5, nargout=0)
            self.eng.setXParam(gl, "cStem", 2.5e5, nargout=0)
            self.eng.setXParam(gl, "tCanSum", 3000, nargout=0)

        # Set solver options with specified tolerances
        options = {"rtol": rel_tol, "atol": abs_tol}

        # Solve the GreenLight model using the ode15s solver
        self.eng.solveFromFile(gl, "ode15s", options, nargout=0)

        # Change the time resolution of the GreenLight model output to 300 seconds
        gl = self.eng.changeRes(gl, float(300), nargout=1)

        # Convert the GreenLight model object to a JSON string
        json_data = self.eng.glObjToJson(gl)

        # Save the GreenLight model object and JSON string to files if specified
        if save_file:

            # Save the GreenLight model object to a .mat file
            self.eng.save(filename, nargout=0)

            # Save the GreenLight JSON string to a .json file
            self.save_to_json(json_data, filename)

        # Load the JSON string into a Python dictionary
        gl_dict = json.loads(json_data)

        # Return the GreenLight model output as a dictionary
        return gl_dict

    def update_params(self, param_dict):
        """
        Update the values of parameters in the given dictionary, overwriting the default values.

        Args:
            param_dict (dict): A dictionary that maps parameter names to their values.

        Returns:
            dict: An updated dictionary with evaluated values for formula parameters and converted values for non-formula parameters.
        """
        # Iterate through the parameter dictionary
        for key, value in list(
            param_dict.items()
        ):  # Use list() to create a snapshot of items
            # If the value is a string, attempt to evaluate the formula
            if isinstance(value, str):
                para_list = self.params_from_string(value)

                # If all parameters are in the parameter dictionary, evaluate the formula
                if all(elem in param_dict.keys() for elem in para_list):
                    result = self.formula_result(param_dict, value, para_list)
                    param_dict[key] = result
                else:
                    # Delete the key if some parameters are missing

                    del param_dict[key]

            # If the value is not a string, convert it to a float
            else:
                param_dict[key] = float(value)

        # Remove the "boiler" key if present
        param_dict.pop("boiler", "")

        return param_dict

    def calculate_energy_consumption(self, gl, *array_keys):
        """
        Calculate the energy consumption for the relevant parameters.

        Args:
            gl: A GreenLight model instance.
            array_keys: A list of parameters to be calculated.

        Returns:
            The energy consumption in MJ.
        """

        # Get the first array and extract the time sequence
        array1 = np.array(gl["a"][array_keys[0]]["val"])
        time_sequence = array1[:, 0]

        # Initialize combined_array with the same shape as array1, filled with zeros
        combined_array = np.zeros_like(array1)

        # Iterate through the keys and add the corresponding arrays to the combined_array
        for key in array_keys:
            array_n = np.array(gl["a"][key]["val"])
            combined_array += array_n

        # Calculate energy consumption using the trapezoidal rule, and convert the result to MJ
        energy_consumption = np.trapz(combined_array[:, 1], time_sequence) / 1e6

        return energy_consumption

    def quit(self):
        """Stop the MATLAB engine."""
        self.eng.quit()

    def default_output_folder(self):
        """Return the default output folder path for the GreenLight model."""
        return os.path.join(self.current_folder, "GreenLight", "Output")

    def data_folder(self):
        """Return the data folder path for the GreenLight model."""
        return os.path.join(
            self.current_folder, "GreenLight", "Code", "inputs", "energyPlus", "data"
        )

    def makeArtificialInput(self, length):
        # make an artifical dataset to use as input for a GreenLight instance
        #   length  - length of desired dataset (days)
        #   weather  will be a matrix with 9 columns, in the following format:
        #       weather[:,0]    timestamps of the input [datenum] in 5 minute intervals
        #       weather[:,1]    radiation     [W m^{-2}]  outdoor global irradiation
        #       weather[:,2]    temperature   [°C]        outdoor air temperature
        #       weather[:,3]    humidity      [kg m^{-3}] outdoor vapor concentration
        #       weather[:,4]    co2 [kg{CO2} m^{-3}{air}] outdoor CO2 concentration
        #       weather[:,5]    wind        [m s^{-1}] outdoor wind speed
        #       weather[:,6]    sky temperature [°C]
        #       weather[:,7]    temperature of external soil layer [°C]
        #       weather[:,8]    daily radiation sum [MJ m^{-2} day^{-1}]

        length = np.ceil(length).astype(int)
        weather = np.empty((length * 288, 9))
        time = np.arange(0, length * 86400, 300)
        weather[:, 0] = self.generate_datenum_list(737485.5, length, 300)
        weather[:, 1] = 350 * np.maximum(0, np.sin(time * 2 * np.pi / 86400))
        weather[:, 2] = 5 * np.sin(time * 2 * np.pi / 86400) + 15
        weather[:, 3] = 0.006 * np.ones(length * 288)
        weather[:, 4] = self.co2ppm2dens(weather[:, 2], 410)
        weather[:, 5] = np.ones(length * 288)
        weather[:, 6] = weather[:, 2] - 20
        weather[:, 7] = 20 * np.ones(length * 288)

        # convert timestamps to datenum
        # weather[:, 0] = time / 86400 + 1
        weather[:, 8] = self.day_light_sum(weather[:, 0], weather[:, 1])

        return weather

    def co2ppm2dens(self, temp, ppm):
        # CO2PPM2DENS Convert CO2 molar concetration [ppm] to density [kg m^{-3}]
        #
        # Usage:
        #   co2Dens = co2ppm2dens(temp, ppm)
        # Inputs:
        #   temp        given temperatures [°C] (numeric vector)
        #   ppm         CO2 concetration in air (ppm) (numeric vector)
        #   Inputs should have identical dimensions
        # Outputs:
        #   co2Dens     CO2 concentration in air [kg m^{-3}] (numeric vector)
        #
        # Calculation based on ideal gas law pV=nRT, with pressure at 1 atm
        #
        # David Katzin, Wageningen University
        # david.katzin@wur.nl
        # david.katzin1@gmail.com

        R = 8.3144598  # molar gas constant [J mol^{-1} K^{-1}]
        C2K = 273.15  # conversion from Celsius to Kelvin [K]
        M_CO2 = 44.01e-3  # molar mass of CO2 [kg mol^-{1}]
        P = 101325  # pressure (assumed to be 1 atm) [Pa]

        # number of moles n=m/M_CO2 where m is the mass [kg] and M_CO2 is the
        # molar mass [kg mol^{-1}]. So m=p*V*M_CO2*P/RT where V is 10^-6*ppm
        co2Dens = P * 10**-6 * ppm * M_CO2 / (R * (temp + C2K))

        return co2Dens

    def day_light_sum(self, time, rad):
        """
        Calculate the light sum from the sun [MJ m^{-2} day^{-1}] for each day.
        These values will be constant for each day, and change at midnight.

        Inputs:
            time - timestamps of radiation data (datenum format).
                These timestamps must be in regular intervals
            rad  - corresponding radiation data (W m^{-2})

        Output:
            lightSum - daily radiation sum, with the same timestamps of time (MJ m^{-2} day^{-1})
        """

        interval = (time[1] - time[0]) * 86400  # interval in time data, in seconds

        mn_before = 0  # the midnight before the current point
        mn_after = (
            np.where(np.diff(np.floor(time)) == 1)[0][0] + 1
        )  # the midnight after the current point

        light_sum = np.zeros(len(time))

        for k in range(len(time)):

            # sum from midnight before until midnight after (not including)
            light_sum[k] = np.sum(rad[mn_before:mn_after])

            if k == mn_after - 1:  # reached new day
                mn_before = mn_after
                new_day_indices = np.where(
                    np.diff(np.floor(time[mn_before + 1 :])) == 1
                )[0]

                if len(new_day_indices) > 0:
                    mn_after = new_day_indices[0] + mn_before + 2
                else:
                    mn_after = len(time)

        # convert to MJ/m2/day
        light_sum = light_sum * interval * 1e-6

        return light_sum

    def generate_datenum_list(self, start_datenum, num_days, interval_secs):
        """
        Generates a list of MATLAB datenums starting from the specified start_datenum
        and with the specified time interval and number of days.

        Args:
        - start_datenum (float): The datenum to start generating from.
        - num_days (int): The number of days to generate datenums for.
        - interval_secs (int): The time interval in seconds between each datenum.

        Returns:
        - datenum_list (list of floats): The list of MATLAB datenums for the specified time interval and number of days.
        """

        # Calculate the number of intervals for the specified time range
        num_intervals = int(num_days * 24 * 60 * 60 / interval_secs)

        # Construct the datetime object corresponding to the start_datenum
        start_datetime = (
            datetime.datetime.fromordinal(int(start_datenum))
            + datetime.timedelta(days=start_datenum % 1)
            - datetime.timedelta(days=366)
        )

        # Generate the list of datenums for the specified time interval and number of days
        datenum_list = []
        for i in range(num_intervals):
            current_datetime = start_datetime + datetime.timedelta(
                seconds=interval_secs * i
            )
            current_datenum = current_datetime.toordinal() + (
                current_datetime
                - datetime.datetime.fromordinal(current_datetime.toordinal())
            ).total_seconds() / (24 * 60 * 60)
            datenum_list.append(current_datenum)
        datenum_array = np.array(datenum_list)

        return datenum_array

    def params_from_string(self, formular_str):
        """
        Extract all the parameters (i.e., variables) from the given formula string.

        Args:
        formular_str (str): The formula string to extract parameters from.

        Returns:
        list: A list of matched words, excluding "pi" and "exp".
        """
        # Regular expression pattern to match parameters
        pattern = r"\b[a-zA-Z]+[a-zA-Z0-9]*\b"
        # Find all matches of the pattern in the formula string
        matched_words = re.findall(pattern, formular_str)
        # Remove "pi" and "exp" from the list of matched words
        matched_words = [word for word in matched_words if word not in ("pi", "exp")]
        return matched_words

    def formula_result(self, param_dict, formula_str, para_list):
        """
        Calculate the dependent parameters for the GreenLight model using the given formula string and parameters.
        Dependent parameters are parameters that depend on the setting of another parameters.

        Args:
            param_dict (dict): A dictionary that maps parameter names to their values.
            formula_str (str): The formula string to calculate.
            para_list (list): A list of parameter names used in the formula string.

        Returns:
            float: The evaluated result of the formula.
        """
        # Create a dictionary of keyword arguments for the evaluation of the formula
        kwargs = {para: param_dict[para] for para in para_list if para != "pi"}
        # Parse the formula string into a SymPy expression
        # print(formula_str)
        formula_expr = parse_expr(formula_str)
        # Calculate the formula expression and return the result as a float

        return float(formula_expr.evalf(subs=kwargs))

    def save_to_json(self, json_data, filename=None):
        """
        Save the data to a JSON file.

        Args:
        json_data: The JSON data to be saved.
        filename: The name of the file to save the data to. Defaults to "data".

        Returns:
        None
        """

        # Convert the JSON string to a Python dictionary
        data = json.loads(json_data)

        # Convert the dictionary back to a JSON string without extra quotes and backslashes
        clean_json_str = json.dumps(data, ensure_ascii=False)

        # If no filename is provided, use "data.json" as the default
        filename = filename or "data"

        # Save the cleaned JSON string to a file
        with open(
            os.path.join(self.output_folder, f"{filename}.json"), "w", encoding="utf-8"
        ) as f:
            f.write(clean_json_str)

    def find_comment(self, var_name):
        """Find the comment associated with the given variable name.

        Args:
        var_name (str): The name of the variable to find the comment for.

        Returns:
        str: The comment associated with the given variable name.
        """
        with open(__file__, "r") as file:
            lines = file.readlines()

        for line in lines:
            if f'"{var_name}"' in line:

                comment = re.findall(r"#.*", line)
                if comment:
                    return comment[0].strip()
        return ""

    def print_all_dicts(self):
        """
        Print all dictionaries stored in the class.

        Prints the names, keys, values, and comments (if any) of all dictionaries stored in the class.
        """
        all_dicts = self.get_all_dicts()
        for name, d in all_dicts.items():
            print(f"\033[1m\033[34m{name}:\033[0m")
            for key, value in d.items():
                comment = self.find_comment(key)
                print(f"{key: <20} {value: <20} {comment}")
            print(f"{'--' * 40}\n")

    def get_all_dicts(self):
        """
        Get all dictionaries stored in the class.

        Returns:
        dict: A dictionary containing all dictionaries stored in the class.
        """
        return {
            "general_parameters": self.general_parameters,
            "construction_parameters": self.construction_parameters,
            "ventilation_parameters": self.ventilation_parameters,
            "roof_parameters": self.roof_parameters,
            "whitewash_parameters": self.whitewash_parameters,
            "shadow_screen_parameters": self.shadow_screen_parameters,
            "thermal_screen_parameters": self.thermal_screen_parameters,
            "blackout_screen_parameters": self.blackout_screen_parameters,
            "floor_parameters": self.floor_parameters,
            "soil_parameters": self.soil_parameters,
            "heating_system_parameters": self.heating_system_parameters,
            "active_climate_control_parameters": self.active_climate_control_parameters,
            "dependant_parameters": self.dependant_parameters,
            "canopy_photosynthesis_parameters": self.canopy_photosynthesis_parameters,
            "carbohydrates_buffer_parameters": self.carbohydrates_buffer_parameters,
            "crop_development_parameters": self.crop_development_parameters,
            "control_parameters": self.control_parameters,
            "growpipe_parameters": self.growpipe_parameters,
            "other_parameters": self.other_parameters,
        }

    def help(self, function_name):
        # Define a dictionary that maps function names to their corresponding functions
        function_map = {
            "add_paths": self.add_paths,
            "update_params": self.update_params,
            "run_green_light": self.run_green_light,
            "calculate_energy_consumption": self.calculate_energy_consumption,
            "quit": self.quit,
            "makeArtificialInput": self.makeArtificialInput,
            "co2ppm2dens": self.co2ppm2dens,
            "day_light_sum": self.day_light_sum,
            "generate_datenum_list": self.generate_datenum_list,
            "params_from_string": self.params_from_string,
            "formula_result": self.formula_result,
            "default_output_folder": self.default_output_folder,
            "data_folder": self.data_folder,
            "save_to_json": self.save_to_json,
            "find_comment": self.find_comment,
            "get_all_dicts": self.get_all_dicts,
            "print_all_dicts": self.print_all_dicts,
        }

        # Check if the function_name exists in the function_map dictionary
        if function_name in function_map:
            # Get the corresponding function object from the dictionary
            function = function_map[function_name]

            # Print the function name in bold blue
            print(f"\033[1m\033[34mFunction: {function_name}:\n\033[0m")

            # Get the docstring of the function, remove leading and trailing whitespaces
            docstring = function.__doc__.strip()
            # Format the docstring by removing left indentation
            formatted_docstring = "\n".join(
                line.lstrip() for line in docstring.split("\n")
            )
            # Print the formatted docstring
            print(f"{formatted_docstring}\n")

        else:
            # If the function name is not in the function_map, print an error message
            print("No help available for this function.")
