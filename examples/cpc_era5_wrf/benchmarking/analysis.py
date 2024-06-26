import os
import h5py
import xarray as xr
import matplotlib.pyplot as plt

from evaluation.plots import plot_maps, plot_cdfs, plot_psds
from evaluation.metrics import *
from utils import create_folder, get_spatial_lengths

def load_data(data_dir, filenames):
    data = {}
    for name, filename in filenames.items():
        with h5py.File(os.path.join(data_dir, filename), "r") as f:
            data[name] = {
                "precip": f["precip"][:, :, :],
                "lons": f["longitude"][:],
                "lats": f["latitude"][:],
                "times": xr.open_dataset(os.path.join(data_dir, filename)).time.values
            }
    return data

def preprocess_data(data, time_index, Nx, Ny):
    for key in data.keys():
        data[key]['precip'] = data[key]['precip'][time_index, :Ny, :Nx]
        data[key]['times'] = data[key]['times'][time_index]
    return data

def create_forecast_dicts(data, x_length, y_length):
    return [
        {"name": name, "data": values['precip'], "x_length": x_length, "y_length": y_length}
        for name, values in data.items()
    ]

def print_metrics(reference, forecasts, unit):
    metrics = [
        {
            "name": "MAE ({})".format(unit),
            "func": lambda ref, pred: mean_absolute_error(ref["data"], pred["data"])
        },
        {
            "name": "RMSE ({})".format(unit),
            "func": lambda ref, pred: root_mean_squared_error(ref["data"], pred["data"])
        },
        {
            "name": "logCDF-l2 (no units)",
            "func": lambda ref, pred: logcdf_distance(ref["data"], pred["data"], "l2")
        },
        {
            "name": "logCDF-max (no units)",
            "func": lambda ref, pred: logcdf_distance(ref["data"], pred["data"], "max")
        },
        {
            "name": "Perkins Skill Score (no units)",
            "func": lambda ref, pred: perkins_skill_score(ref["data"], pred["data"])
        },
        {
            "name": "CRPS ({})".format(unit),
            "func": lambda ref, pred: crps(ref["data"], pred["data"])
        },
        {
            "name": "logPSD-l2 (no units)",
            "func": lambda ref, pred: logpsd_distance(
                ref["data"], ref["x_length"], ref["y_length"],
                pred["data"], pred["x_length"], pred["y_length"],
                "l2"
            )
        },
        {
            "name": "logPSD-max (no units)",
            "func": lambda ref, pred: logpsd_distance(
                ref["data"], ref["x_length"], ref["y_length"],
                pred["data"], pred["x_length"], pred["y_length"],
                "max"
            )
        },
    ]

    for metric in metrics:
        print("+ "+metric["name"]+":")
        for forecast in forecasts:
            value = metric["func"](reference, forecast)
            print("  - {}: {:.3f}".format(forecast['name'], value))
        print("\n")

def main(data_dir, filenames, time_index, Nx, Ny, plot_time):
    # Load and preprocess data
    data = load_data(data_dir, filenames)
    data = preprocess_data(data, time_index, Nx, Ny)

    # Extract spatial extents
    lons, lats = data['CombiPrecip']['lons'], data['CombiPrecip']['lats']
    extent = (lons.min(), lons.max(), lats.min(), lats.max())
    x_length, y_length = get_spatial_lengths(lons, lats)

    # Prepare forecast dictionaries
    forecasts = create_forecast_dicts(data, x_length, y_length)

    # Plotting
    script_dir = os.path.dirname(os.path.realpath(__file__))
    figs_dir = os.path.join(script_dir, "figs")
    create_folder(figs_dir)

    # Plot maps
    arrays = [data[key]['precip'][plot_time, :, :] for key in filenames.keys()]
    
    print("Check times:")
    time_arrays = [data[key]['times'] for key in filenames.keys()]
    for times in time_arrays:
        print(times[-1])
    
    titles = (None, None, None, None)
    # titles = list(filenames.keys())
    extents = [extent] * len(arrays)
    fig, _ = plot_maps(arrays, titles, extents)
    fig.savefig(os.path.join(figs_dir, "maps_comparison.png"))

    # Plot CDFs
    arrays = [data[key]['precip'] for key in filenames.keys()]
    labels = list(filenames.keys())
    fig, _ = plot_cdfs(arrays, labels)
    fig.savefig(os.path.join(figs_dir, "cdf_comparison.png"))

    # Plot PSDs
    spatial_lengths = [(x_length, y_length) for _ in range(len(arrays))]
    fig, _ = plot_psds(arrays, labels, spatial_lengths, min_threshold=1e-10)
    fig.savefig(os.path.join(figs_dir, "psd_comparison.png"))

    # Print metrics
    reference = forecasts.pop(2)  # Assuming the first item is the reference
    print_metrics(reference, forecasts, "mm/h")

if __name__ == "__main__":
    data_dir = "/work/FAC/FGSE/IDYST/tbeucler/downscaling/mlima/data/test_data"
    filenames = {
        "QM (all)": "era5_qm_all.h5",
        "QM (point-to-point)": "era5_qm_point.h5",
        "CombiPrecip": "cpc.h5",
        "WRF": "wrf.h5",
        # "ERA5 (low-pass)": "era5_low-pass.h5",
        # "paired_qm_all": "paired_qm_all.h5",
        # "unpaired_qm_all": "unpaired_qm_all.h5",
        # "paired_qm_point": "paired_qm_point.h5",
        # "unpaired_qm_point": "unpaired_qm_point.h5",
    }
    time_index = slice(0, 48)
    Nx = 336
    Ny = 224
    plot_time = -10

    main(data_dir, filenames, time_index, Nx, Ny, plot_time)
