import numpy as np
import time
from gl_model import GreenLightModel


if __name__ == "__main__":
    start_time = time.time()

    # Instantiate the GreenLightModel with custom parameter values (optional)
    model = GreenLightModel()

    p = {
        # Parameters can be added here, more settings can be found in the GreenLight model attributes, using print_all_dicts() function.
        "psi": 22,  # Mean greenhouse cover slope
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
        "co2SpDay": 1000,  # CO2 setpoint during the light period [ppm]
        "tSpNight": 18.5,  # temperature set point dark period [°C]
        "tSpDay": 19.5,  # temperature set point light period [°C]
        "rhMax": 87,  # maximum relative humidity [ %]
        "ventHeatPband": 4,  # P-band for ventilation due to high temperature [°C]
        "ventRhPband": 50,  # P-band for ventilation due to high relative humidity [ % humidity]
        "thScrRhPband": 10,  # P-band for screen opening due to high relative humidity [ % humidity]
        "lampsOn": 0,  # time of day (in morning) to switch on lamps [h]
        "lampsOff": 18,  # time of day (in evening) to switch off lamps 	[h]
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
        seasonLength=1 / 24 / 6,  # season length in 5 minute intervals
        firstDay=1,  # Beginning of season (days since January 1)
        isMature=False,  # Start with a mature crop, use false to start with a small crop
        lampType="led",  # 'led', 'hps', or 'none'
    )

    # Energy consumption of the lamps [MJ m^{-2}]
    lampIn = model.calculate_energy_consumption(gl, "qLampIn", "qIntLampIn")

    # Energy consumption of the boiler, boilIn [MJ m^{-2}]
    boilIn = model.calculate_energy_consumption(gl, "hBoilPipe", "hBoilGroPipe")

    # CO2 Use,co2inj,kg/m2
    co2inj = model.calculate_energy_consumption(gl, "mcExtAir")

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
