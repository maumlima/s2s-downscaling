import os

import ml_collections


def get_config():
    config = ml_collections.ConfigDict()

    # Data directories
    base = "mlima-path/"
    config.train_data_dir = os.path.join(base, "data/train_data")
    config.test_data_dir = os.path.join(base, "data/test_data")
    config.sim_data_dir = os.path.join(base, "data/simulations/quantile_mapping")

    # Quantile Mapping parameters
    config.n_quantiles = 500
    config.method_point = "point_to_point"

    return config
