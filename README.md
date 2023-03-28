# GreenLightModel

The GreenLightModel class is a Python wrapper for the [GreenLight](https://github.com/davkat1/GreenLight) MATLAB model, which allows for running simulations of greenhouse environments with supplemental lighting. The resulting model simulations are outputted as a Python dictionary and saved as a JSON file, enabling direct use within Python programs and the ability to perform various calculations with the obtained results.

## Table of Contents

- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Example](#example)
- [Functions](#functions)
  - [Core Functions](#core-functions)
    - [add_paths](#add_paths)
    - [update_params](#update_params)
    - [run_green_light](#run_green_light)
    - [calculate_energy_consumption](#calculate_energy_consumption)
    - [quit](#quit)
  - [Non-core Functions](#non-core-functions)
    - [makeArtificialInput](#makeartificialinput)
    - [co2ppm2dens](#co2ppm2dens)
    - [day_light_sum](#day_light_sum)
    - [generate_datenum_list](#generate_datenum_list)
    - [params_from_string](#params_from_string)
    - [formula_result](#formula_result)
    - [default_output_folder](#default_output_folder)
    - [data_folder](#data_folder)
    - [save_to_json](#save_to_json)
    - [find_comment](#find_comment)
    - [get_all_dicts](#get_all_dicts)
    - [print_all_dicts](#print_all_dicts)
    - [help](#help)
- [Attributes](#Attributes)
- [References](#references)
- [License](#license)

## Installation

There are two ways to install this application:

**Method 1 (Recommended):**

Clone the repository and install the dependencies using `pip`.

```shell
$ git clone https://github.com/greenpeer/GreenLightModel
$ cd GreenLightModel
$ pip install -r requirements.txt
```

**Method 2:**

To use the GreenLightModel class, you will need to have the [GreenLight](https://github.com/davkat1/GreenLight) and [DyMoMa](https://github.com/davkat1/DyMoMa/) models and [GreenLight_Extensions](https://github.com/greenpeer/GreenLight_Extensions) downloaded on your local machine. Once you have downloaded this repository, you should put it in the same folder as the GreenLight and DyMoMa models.

Here are the steps to get started:

1. Download the [GreenLight](https://github.com/davkat1/GreenLight) and [DyMoMa](https://github.com/davkat1/DyMoMa/) models and [GreenLight_Extensions](#https://github.com/greenpeer/GreenLight_Extensions) on your computer.
2. Download the repository containing the GreenLightModel class.
3. Place the GreenLightModel class repository in the same folder as the GreenLight and DyMoMa models.

After completing these steps, you will be ready to use the GreenLightModel class in your Python programs.

## Dependencies

Ensure MATLAB R2016b or a more recent version installed on your local machine.You can download it from the [official website](https://www.mathworks.com/products/matlab.html).

```bash
git clone https://github.com/davkat1/GreenLight.git
git clone https://github.com/davkat1/DyMoMa.git
```

Install the required Python packages by running the following command in your terminal or command prompt:

```bash
pip install -r requirements.txt
```

To install the required MATLAB Engine API for Python package, you can use `pip`:

```bash
python -m pip install matlabengine
```

## Usage

To use the GreenLightModel class, import it in your Python script:

```python
from gl_model import GreenLightModel
```

Create an instance of the GreenLightModel class:

```python
# Instantiate the GreenLightModel with custom parameter values (optional)
model = GreenLightModel()

# Run the model
gl = model.run_green_light(
        filename="sample",  # add file name for saving file
        weatherInput="bei",  # Choose name of location, see folder inputs/energyPlus/data/
        seasonLength=(1 / 24 / 6) * 1,  # season length in days
        firstDay=1,  # Beginning of season (days since January 1)
        isMature=True,  # Start with a mature crop, use false to start with a small crop
        lampType="led",  # 'led', 'hps', or 'none'
    )
```

You can now use the various methods provided by the GreenLightModel class.

## Example

```python
import numpy as np
import time
from gl_model import GreenLightModel


if __name__ == "__main__":
    start_time = time.time()

    # Instantiate the GreenLightModel with custom parameter values (optional)
    model = GreenLightModel()

    p = {
        # more setting parameters can be found in the GreenLightModel class attributes, using print_all_dicts() function
        "psi": 42,  # Mean greenhouse cover slope
        "aFlr": 4e4,  # Floor area of greenhouse  [m^{2}]
        "aCov": 4.84e4,  # Surface of the cover including side walls [m^{2}]
        "hAir": 6.3,  # Height of the main compartment [m] (the ridge height is 6.5, screen is 20 cm below it)
        "hGh": 6.905,  # Average height of the greenhouse [m],Each triangle in the greenhouse roof has width 4m, angle 22°, so height of 0.81m. The ridge is 6.5 m high
        "aRoof": 0.1169 * 4e4,  # Maximum roof ventilation area
        "hVent": 1.3,  # Vertical dimension of single ventilation opening [m]
        "cDgh": 0.75,  # Ventilation discharge coefficient [-]
        "lPipe": 1.25,  # Length of heating pipes per gh floor area [m m^{-2}]
        "phiExtCo2": 7.2e4
        * 4e4
        / 1.4e4,  # Capacity of CO2 injection for the entire greenhouse [mg s^{-1}], this is 185 kg/ha/hour, based on [1] and adjusted to 4 ha
        "hElevation": 100,  #  Altitude of greenhouse m above sea level
        "co2SpDay": 1000,  # CO2 setpoint during the light period [ppm]
        "tSpNight": 18.5,  # temperature set point dark period [°C]
        "tSpDay": 19.5,  # temperature set point light period [°C]
        "rhMax": 67,  # maximum relative humidity [ %]
        "ventHeatPband": 4,  # P-band for ventilation due to high temperature [°C]
        "ventRhPband": 50,  # P-band for ventilation due to high relative humidity [ % humidity]
        "thScrRhPband": 10,  # P-band for screen opening due to high relative humidity [ % humidity]
        "lampsOn": 0,  # time of day (in morning) to switch on lamps [h]
        "lampsOff": 12,  # time of day (in evening) to switch off lamps 	[h]
        "lampsOffSun": 400,  # lamps are switched off if global radiation is above this value [W m^{-2}]
        "lampRadSumLimit": 10,  # Predicted daily radiation sum from the sun where lamps are not used that day [MJ m^{-2} day^{-1}]
        "boiler": 300,  # big boiler, capacity of boiler [W]
        "pBoil": "boiler * aFlr",  # Capacity of boiler for the entire greenhouse [W]
    }

    # update the parameters
    model.p.update(p)

    # Run the model
    gl = model.run_green_light(
        filename="sample",  # add file name for saving file
        weatherInput="bei",  # Choose name of location, see folder inputs/energyPlus/data/
        seasonLength=(1 / 24 / 6) * 1,  # season length in days
        firstDay=1,  # Beginning of season (days since January 1)
        isMature=True,  # Start with a mature crop, use false to start with a small crop
        lampType="led",  # 'led', 'hps', or 'none'
    )

    # Energy consumption of the lamps [MJ m^{-2}]
    lampIn = model.calculate_energy_consumption(gl, "qLampIn", "qIntLampIn")

    # Energy consumption of the boiler, boilIn [MJ m^{-2}]
    boilIn = model.calculate_energy_consumption(gl, "hBoilPipe", "hBoilGroPipe")

    # CO2 Use,co2inj,kg/m2
    co2inj = model.calculate_energy_consumption(gl, "mcExtAir")

    # print(gl)
    print("--" * 40)
    print(f"Energy consumption of the lamps: {lampIn} MJ m^{-2}")
    print(f"Energy consumption of the boiler: {boilIn} MJ m^{-2}")
    print(f"CO2 Use: {co2inj} kg m^{-2}")
    print("--" * 40)

    # Stop the MATLAB engine
    model.quit()

    end_time = time.time()

    print("Time taken: {:.2f} seconds".format(end_time - start_time))

    # Get all setting parameters for the model
    # model.print_all_dicts()

    # Get help message for the calculate_energy_consumption function
    # model.help("calculate_energy_consumption")

```

## Functions

The GreenLightModel class provides the following methods:

### Core Functions:

- [`add_paths()`](#add_paths): Adds required paths to MATLAB's search path.
- [`update_params(param_dict)`](#update_params): Update the values of parameters in the given dictionary, overwriting the default values.
- [`run_green_light(lamp_type=None, weather=None, filename=None, param_names=None, param_vals=None, is_mature=False)`](#run_green_light): Runs the GreenLight model with the given parameters,returns the GreenLight model with the completed simulation in python dictionary format. Data of this simulation is given in 5-minute intervals.
- [`calculate_energy_consumption(gl, *array_keys)`](#calculate_energy_consumption): Calculate the energy consumption for the given parameters.
- [`quit()`](#quit): Stop the MATLAB engine.

---

#### `add_paths`

Add required paths to MATLAB's search path.

```python
add_paths()
```

##### Returns

- None

---

#### `update_params`

Update the values of parameters in the given dictionary, overwriting the default values.

```python
updated_param_dict = update_params(param_dict)
```

##### Args

- `param_dict` (dict): A dictionary that maps parameter names to their values.

##### Returns

- `updated_param_dict` (dict): An updated dictionary with evaluated values for formula parameters and converted values for non-formula parameters.

---

#### `run_green_light`

Runs the Green Light simulation with specified parameters and weather input.

```python
gl = run_green_light(
    filename="output_file",
    weatherInput="bei",
    seasonLength=1 / 24 / 6,
    firstDay=1,
    isMature=True,
    lampType="led",
)
```

##### Args

- `filename`: (str) The file name for saving the output data. Default is an empty string, which means the output data will not be saved.
- `weatherInput`: (str) The input file name for the weather data, without the file extension. Default is "bei".
- `seasonLength`: (float) The length of the season in fraction of a year. Default is 1/24/6.
- `firstDay`: (int) The first day of the simulation. Default is 1.
- `isMature`: (bool) Whether the crop is mature. Default is True.
- `lampType`: (str) The type of lamp used in the simulation. Default is "led". Available options are "hps", "led", and "none".

##### Variables within the function

- `lamp_type`: Lamp type to simulate, may be 'hps', 'led', or 'none'. Default value is 'none'.
- `weather`: Weather inputs for the model. If this argument is empty, artificial weather data for a 5-day season will be generated. If this argument is a scalar number, artificial data will be generated for as many days as this scalar number. Otherwise, weather needs to be a 9-column matrix in the following format:
  - weather(:,1): timestamps of the input [datenum] in 5-minute intervals
  - weather(:,2): radiation [$W m^{-2}$] outdoor global irradiation
  - weather(:,3): temperature [°C] outdoor air temperature
  - weather(:,4): humidity [$kg m^{-3}$] outdoor vapor concentration
  - weather(:,5): co2 [$kg{CO2} m^{-3}{air}$] outdoor CO2 concentration
  - weather(:,6): wind [$m s^{-1}$] outdoor wind speed
  - weather(:,7): sky temperature [°C]
  - weather(:,8): temperature of external soil layer [°C]
  - weather(:,9): daily radiation sum [$MJ m^{-2} day^{-1}$]
  - weather(:,10): elevation [m above sea level] (optional, default is 0)
- `filename`: Name of the file where the simulation results will be saved. If empty or blank (''), no file will be saved.
- `param_names`: Array of strings with names of parameters to modify beyond their default values. Example: ["lampsOn" "lampsOff"]. NOTE: "dependent parameters" (those defined in setDepParams) should be changed by changing their defining parameters. For example, setting aPipe as 0 should be done by setting lPipe or phiPipeE as 0. See setDepParams for a list of dependent parameters.
- `param_vals`: Array of values (corresponding to param_names) with modified parameter values.
- `is_mature`: If true, simulation will start with a mature crop. Default is false.

##### Returns

- `gl`: (dict) A Python dictionary containing the GreenLight model output with the completed simulation. Data of this simulation is given in 5-minute intervals.

---

#### `calculate_energy_consumption`

Calculate the energy consumption for the relevant parameters.

```python
energy_consumption = calculate_energy_consumption(gl, *array_keys)
```

##### Args

- `gl`: A GreenLight model instance.
- `array_keys`: A list of keys representing the arrays to be combined and analyzed.

##### Returns

- `energy_consumption` (float): The energy consumption in MJ.

---

#### `quit`

Stop the MATLAB engine.

```python
quit()
```

##### Returns

- None

---

### Non-core Functions:

- [`makeArtificialInput`](#makeartificialinput): Make an artificial dataset to use as input for a GreenLight instance.
- [`co2ppm2dens`](#co2ppm2dens): Convert CO2 molar concentration [ppm] to density [kg m^{-3}].
- [`day_light_sum`](#day_light_sum): Calculate the light sum from the sun [MJ m^{-2} day^{-1}] for each day. These values will be constant for each day, and change at midnight.
- [`generate_datenum_list`](#generate_datenum_list): Generates a list of MATLAB format datenums starting from the specified start_datenum and with the specified time interval and number of days.
- [`params_from_string()`](#params_from_string): Extracts all the parameters (i.e., variables) from the given formula string.
- [`formula_result()`](#formula_result): Calculate the dependent parameters for the GreenLight model using the given formula string and parameters.
- [`default_output_folder()`](#default_output_folder): Returns the default output folder path for the GreenLight model.
- [`data_folder()`](#data_folder): Returns the data folder path for the GreenLight model.
- [`save_to_json(json_data, filename=None)`](#save_to_json): Saves the data to a JSON file.
- [`print_all_dicts()`](#print_all_dicts): Prints all parameters in the dictionaries along with their keys, values, and comments.
- [`find_comment(var_name)`](#find_comment): Finds and returns the comment associated with a variable in the source code.
- [`help()`](#help): Prints the help text (docstring) describing the class and its dictionaries.

---

#### `makeArtificialInput`

Make an artificial dataset to use as input for a GreenLight instance.

```python
weather = makeArtificialInput(length)
```

##### Args

- `length`: length of desired dataset (days)

##### Returns

- `weather`: a matrix with 9 columns, in the following format:
  - `weather[:,0]`: timestamps of the input [datenum] in 5-minute intervals
  - `weather[:,1]`: radiation [W m^{-2}] outdoor global irradiation
  - `weather[:,2]`: temperature [°C] outdoor air temperature
  - `weather[:,3]`: humidity [kg m^{-3}] outdoor vapor concentration
  - `weather[:,4]`: CO2 [kg{CO2} m^{-3}{air}] outdoor CO2 concentration
  - `weather[:,5]`: wind [m s^{-1}] outdoor wind speed
  - `weather[:,6]`: sky temperature [°C]
  - `weather[:,7]`: temperature of external soil layer [°C]
  - `weather[:,8]`: daily radiation sum [MJ m^{-2} day^{-1}]

---

#### `co2ppm2dens`

Convert CO2 molar concentration [ppm] to density [kg m^{-3}].

```python
co2Dens = co2ppm2dens(temp, ppm)
```

##### Args

- `temp`: given temperatures [°C] (numeric vector)
- `ppm`: CO2 concentration in air (ppm) (numeric vector)

Inputs should have identical dimensions

##### Returns

- `co2Dens`: CO2 concentration in air [kg m^{-3}] (numeric vector)

---

#### `day_light_sum`

Calculate the light sum from the sun [MJ m^{-2} day^{-1}] for each day. These values will be constant for each day, and change at midnight.

```python
lightSum = day_light_sum(time, rad)
```

##### Args

- `time`: timestamps of radiation data (datenum format). These timestamps must be in regular intervals
- `rad`: corresponding radiation data (W m^{-2})

##### Returns

- `lightSum`: daily radiation sum, with the same timestamps of time (MJ m^{-2} day^{-1})

---

#### `generate_datenum_list`

Generates a list of MATLAB format datenums starting from the specified start_datenum and with the specified time interval and number of days.

```python
datenum_list = generate_datenum_list(start_datenum, num_days, interval_secs)
```

##### Args

- `start_datenum` (float): The datenum to start generating from.
- `num_days` (int): The number of days to generate datenums for.
- `interval_secs` (int): The time interval in seconds between each datenum.

##### Returns

- `datenum_list` (list of floats): The list of MATLAB datenums for the specified time interval and number of days.

---

#### `params_from_string`

Extract all the parameters (i.e., variables) from the given formula string.

```python
params = params_from_string(formular_str)
```

##### Args

- `formular_str` (str): The formula string to extract parameters from.

##### Returns

- `params` (list): A list of matched words, excluding "pi" and "exp".

---

#### `formula_result`

Calculate the dependent parameters for the GreenLight model using the given formula string and parameters. Dependent parameters are parameters that depend on the setting of another parameters.

```python
result = formula_result(param_dict, formula_str, para_list)
```

##### Args

- `param_dict` (dict): A dictionary that maps parameter names to their values.
- `formula_str` (str): The formula string to calculate.
- `para_list` (list): A list of parameter names used in the formula string.

##### Returns

- `result` (float): The evaluated result of the formula.

---

#### `default_output_folder`

Return the default output folder path for the GreenLight model.

```python
output_folder = default_output_folder()
```

##### Returns

- `output_folder` (str): The default output folder path for the GreenLight model.

---

#### `data_folder`

Return the data folder path for the GreenLight model.

```python
data_folder_path = data_folder()
```

##### Returns

- `data_folder_path` (str): The data folder path for the GreenLight model.

---

#### `save_to_json`

Save the data to a JSON file.

```python
save_to_json(json_data, filename=None)
```

##### Args

- `json_data`: The JSON data to be saved.
- `filename` (str, optional): The name of the file to save the data to. Defaults to "data".

##### Returns

- None

---

#### `find_comment`

Find the comment associated with the given variable name.

```python
comment = find_comment(var_name)
```

##### Args

- `var_name` (str): The name of the variable to find the comment for.

##### Returns

- `comment` (str): The comment associated with the given variable name.

---

#### `get_all_dicts`

Get all dictionaries stored in the class.

```python
all_dicts = get_all_dicts()
```

##### Returns

- `all_dicts` (dict): A dictionary containing all dictionaries stored in the class.

---

#### `print_all_dicts`

Print all dictionaries stored in the class.

Prints the names, keys, values, and comments (if any) of all dictionaries stored in the class.

```python
print_all_dicts()
```

##### Returns

- None

---

#### `help`

Get help for the specified function.

```python
help(function_name)
```

##### Args

- `function_name` (str): The name of the function to get help for.

##### Returns

- None

---

## Attributes

- `p`: A dictionary containing various parameters related to greenhouse systems.
- `general_parameters`: A dictionary containing various parameters related to greenhouse systems.
- `control_parameters`: A dictionary containing various parameters related to greenhouse control systems.
- `growpipe_parameters`: A dictionary containing various parameters related to greenhouse growpipe systems.
- `construction_parameters`: A dictionary containing various parameters related to greenhouse construction properties.
- `ventilation_parameters`: A dictionary containing various parameters related to greenhouse ventilation.
- `roof_parameters`: A dictionary containing various parameters related to greenhouse roof.
- `whitewash_parameters`: A dictionary containing various parameters related to greenhouse whitewash.
- `shadow_screen_parameters`: A dictionary containing various parameters related to greenhouse shadow screen.
- `thermal_screen_parameters`: A dictionary containing various parameters related to greenhouse thermal screen.
- `blackout_screen_parameters`: A dictionary containing various parameters related to greenhouse blackout screen.
- `floor_parameters`: A dictionary containing various parameters related to greenhouse floor.
- `soil_parameters`: A dictionary containing various parameters related to greenhouse soil.
- `heating_system_parameters`: A dictionary containing various parameters related to greenhouse heating system.
- `active_climate_control_parameters`: A dictionary containing various parameters related to greenhouse active climate control.
- `dependant_parameters`: A dictionary containingOther parameters that depend on previously defined parameters.
- `canopy_photosynthesis_parameters`: A dictionary containing various parameters related to greenhouse canopy photosynthesis.
- `carbohydrates_buffer_parameters`: A dictionary containing various parameters related to greenhouse carbohydrates buffer.
- `crop_development_parameters`: A dictionary containing various parameters related to greenhouse crop development.
- `other_parameters`: A dictionary containing various other parameters.
- `current_folder` : The folder containing the class source file.
- `output_folder`: The folder where the output files will be saved.

## References:

- David Katzin, Simon van Mourik, Frank Kempkes, and Eldert J. Van Henten. 2020. “GreenLight - An Open Source Model for Greenhouses with Supplemental Lighting: Evaluation of Heat Requirements under LED and HPS Lamps.” Biosystems Engineering 194: 61–81. [https://doi.org/10.1016/j.biosystemseng.2020.03.010](https://doi.org/10.1016/j.biosystemseng.2020.03.010)
- David Katzin. DyMoMa - Dynamic Modelling for MATLAB. Zenodo. [http://doi.org/10.5281/zenodo.3697908](http://doi.org/10.5281/zenodo.3697908)

## License

This project is licensed under the MIT License. See the [LICENSE](https://chat.openai.com/LICENSE) file for more information.
