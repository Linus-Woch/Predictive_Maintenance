import pandas as pd

def load_data(path, sensors=None, bundle=None):

    if sensors is None:
        if bundle is None:
            raise ValueError("Provide sensors or bundle")

        sensors = bundle["sensors"]

    original_sensors = [f"sensor_{i}" for i in range(1,22)]

    columns = (["engine_id", "cycle", "setting_1", "setting_2", "setting_3"] + original_sensors)
    train_data = pd.read_csv(path, sep=r"\s+", header = None, names=columns)

    useless_sensors = [s for s in original_sensors if s not in sensors]
    train_data = train_data.drop(columns=useless_sensors)
    
    # Sorting data by engine and cycle:
    train_data = train_data.sort_values(["engine_id", "cycle"])

    return train_data


def apply_preprocessing(data, bundle):

    data = data.copy()

    settings = bundle["settings"]
    sensors = bundle["sensors"]

    scaled_settings = bundle["settings_scaler"].transform(data[settings])
    data["regime"] = bundle["k_means"].predict(scaled_settings)

    data = data.astype({s: "float64" for s in sensors})

    for regime, scaler in bundle["sensor_scalers"].items():
        regime_rows = data["regime"] == regime

        # Testing: does this regime even exist in that data?
        if regime_rows.any(): 
            data.loc[regime_rows, sensors] = scaler.transform(data.loc[regime_rows, sensors])

    return data
