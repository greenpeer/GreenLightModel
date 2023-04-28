import time
from gl_model import GreenLightModel

if __name__ == "__main__":
    start_time = time.time()

    # Instantiate the GreenLightModel with custom parameter values (optional)
    model = GreenLightModel()

    # Set Innitial values
    gl = {
        "p": {
            "tSpNight": 28.5,  # temperature set point dark period [°C]
            "tSpDay": 29.5,  # temperature set point light period [°C]
        },
    }

    # Run the model
    gl = model.run_green_light(
        filename="sample",  # add file name for saving file
        weatherInput="bei",  # Choose name of location, see folder inputs/energyPlus/data/
        seasonLength=1 / 24 / 6,  # season length in 5 minute intervals
        firstDay=1,  # Beginning of season (days since January 1)
        isMature=False,  # Start with a mature crop, use false to start with a small crop
        lampType="led",  # 'led', 'hps', or 'none'
        initial_gl=gl,
    )

    # Stop the MATLAB engine
    model.quit()

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

    end_time = time.time()

    print("Time taken: {:.2f} seconds".format(end_time - start_time))
