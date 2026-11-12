import pandas as pd

def get_new_features(data, sensors):
    new_features = {}

    def rolling_means(values, window):
        return values.rolling(window=window, min_periods=1).mean()

    def rolling_std(values, window):
        return values.rolling(window=window, min_periods=1).std(ddof=0)

    def slope(values, window):
        prev_values = values.shift(window)
        prev_values = prev_values.fillna(values)

        slopes = (values - prev_values) / window
        return slopes

    def exponential_mean(values):
        return values.ewm(span=20, adjust=False).mean()

    def expanding_mean(values):
        return values.expanding(min_periods=1).mean()
        

    for s in sensors:

        grouped_train = data.groupby("engine_id")[s]

        for w in [5,15,30]:

            # rolling means
            new_features[f"{s}_mean_{w}"] = grouped_train.transform(rolling_means, window=w)
            # rolling std
            new_features[f"{s}_std_{w}"] = grouped_train.transform(rolling_std, window=w)
            # slope
            new_features[f"{s}_slope_{w}"] = grouped_train.transform(slope, window=w)

        # exponential mean
        smoothed = grouped_train.transform(exponential_mean)
        new_features[f"{s}_ewm_20"] = smoothed
        new_features[f"{s}_deviation"] = data[s] - smoothed

        # comparing ewm with beginning reference
        early_values = data[s].where(data["cycle"] <= 20)
        initial = early_values.groupby(data["engine_id"]).transform(expanding_mean)
        new_features[f"{s}_ewm_from_initial"] = smoothed - initial

    new_features = pd.DataFrame(new_features)
    
    return new_features
