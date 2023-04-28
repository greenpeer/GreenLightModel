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
        current_folder (str): The folder containing the class source file.
        output_folder (str): The folder where the output files will be saved.
        eng (MATLABEngine): A reference to the MATLAB engine instance.

    Methods:
        add_paths(): Adds required paths to MATLAB's search path.
        update_params(param_dict):Update the values of parameters in the given dictionary, overwriting the default values.
        run_green_light(filename="",weatherInput="bei",seasonLength=1 / 24 / 6,firstDay=1,isMature=False,lampType="led",initial_gl=None,): Runs the GreenLight model with the given parameters,returns an instance of the GreenLight model with the completed simulation. Data of this simulation is given in 5-minute intervals.
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
        find_comment(var_name): Finds and returns the comment associated with a variable in the source code.
        help(): Prints the help text (docstring) describing the class and its dictionaries.
    """

    def __init__(self, output_folder=None):
        """Initializes an instance of the GreenLightModel class with default or user-specified parameters."""

        # Get the current file and folder paths
        self.current_file = os.path.abspath(__file__)
        self.current_folder = os.path.dirname(self.current_file)

        # Set output folder path for the GreenLight model
        self.output_folder = (
            output_folder if output_folder else self.default_output_folder()
        )

        # If the output folder does not exist, create it
        if not os.path.exists(self.output_folder):
            os.makedirs("folder_name")

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
        isMature=False,
        lampType="led",
        initial_gl=None,
    ):
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
            # Create artificial weather input with default value,length of desired dataset (5 days)
            weather = self.makeArtificialInput(5)

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

        # Set dependent parameters
        self.eng.setDepParams(gl, nargout=0)

        # Set initial state values if the crop is mature
        if isMature:
            self.eng.setParamVal(gl, "x", "cFruit", 2.8e5, nargout=0)
            self.eng.setParamVal(gl, "x", "cLeaf", 0.9e5, nargout=0)
            self.eng.setParamVal(gl, "x", "cStem", 2.5e5, nargout=0)
            self.eng.setParamVal(gl, "x", "tCanSum", 3000, nargout=0)

        # Update the GreenLight model parameters with the new values, if provided
        gl = self.update_params(gl, initial_gl)

        # Set solver options with specified tolerances
        options = {"rtol": rel_tol, "atol": abs_tol}

        # Convert Python dictionary to MATLAB struct
        options_struct = self.eng.struct(options)

        # Solve the GreenLight model using the ode15s solver
        self.eng.solveFromFile(gl, "ode15s", options_struct, nargout=0)

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

    def update_params(self, gl, initial_gl):
        """
        Update the values of parameters in the given dictionary, overwriting the default values.

        Args:
            gl (matlab.object): An original GreenLight model object.
            initial_gl (dict): A dictionary that maps parameter names to their values.

        Returns:
            gl (matlab.object): An matlab.object with updated values.
        """
        for outer_key, outer_value in initial_gl.items():
            if outer_key == "p":
                for inner_key, inner_value in outer_value.items():
                    if not isinstance(inner_value, dict):
                        self.eng.setParam(gl, inner_key, inner_value, nargout=0)
                    else:
                       
                        if inner_value["val"] is not None:
                            self.eng.setParam(gl, inner_key, self.eng.double(inner_value["val"]), nargout=0)
                        
            elif outer_key == "x":
                for inner_key, inner_value in outer_value.items():
                  
                    if isinstance(inner_value, dict):
                        self.eng.setParamVal(
                            gl,
                            outer_key,
                            inner_key,
                            inner_value["val"][-1][-1],
                            nargout=0,
                        )
                    else:
                        self.eng.setParamVal(
                            gl, outer_key, inner_key, inner_value, nargout=0
                        )

        return gl

    def calculate_energy_consumption(self, gl, *array_keys):
        """
        Calculate the energy consumption for the relevant parameters.

        Args:
            gl: A GreenLight model instance.
            array_keys: A list of parameters to be calculated.

        Returns:
            The energy consumption in MJ.
        """
        # Create a dictionary mapping second-level keys to top-level keys in gl
        param_dicts = {
            key2: key
            for key, value in gl.items()
            if (isinstance(value, dict) and key != "t")
            for key2, value2 in value.items()
        }

        # Initialize combined_array with None
        combined_array = None

        # Iterate through the keys and add the corresponding arrays to the combined_array
        for i, key in enumerate(array_keys):
            attrib = param_dicts[key]
            array_n = np.array(gl[attrib][key]["val"])
            if i == 0:
                # For the first array, extract the time sequence and initialize combined_array with zeros
                time_sequence = array_n[:, 0]
                combined_array = np.zeros_like(array_n)

            # Add the current array to the combined_array
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
        """
        make an artifical dataset to use as input for a GreenLight instance
        length  - length of desired dataset (days)
        weather  will be a matrix with 9 columns, in the following format:
            weather[:,0]    timestamps of the input [datenum] in 5 minute intervals
            weather[:,1]    radiation     [W m^{-2}]  outdoor global irradiation
            weather[:,2]    temperature   [°C]        outdoor air temperature
            weather[:,3]    humidity      [kg m^{-3}] outdoor vapor concentration
            weather[:,4]    co2 [kg{CO2} m^{-3}{air}] outdoor CO2 concentration
            weather[:,5]    wind        [m s^{-1}] outdoor wind speed
            weather[:,6]    sky temperature [°C]
            weather[:,7]    temperature of external soil layer [°C]
            weather[:,8]    daily radiation sum [MJ m^{-2} day^{-1}]
        """

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
        """
        CO2PPM2DENS Convert CO2 molar concetration [ppm] to density [kg m^{-3}]

        Usage:
          co2Dens = co2ppm2dens(temp, ppm)
        Inputs:
          temp        given temperatures [°C] (numeric vector)
          ppm         CO2 concetration in air (ppm) (numeric vector)
          Inputs should have identical dimensions
        Outputs:
          co2Dens     CO2 concentration in air [kg m^{-3}] (numeric vector)

        Calculation based on ideal gas law pV=nRT, with pressure at 1 atm
        """

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
