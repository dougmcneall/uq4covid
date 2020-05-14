# Handy utility functions for the analysis manager

import os
import numpy as np
import json as js
from typing import List, Any
from metawards._disease import Disease
from dataclasses import asdict


# Handy short-hand for checking that a list of dictionaries have a minimum set of common keys
def check_common_keys_in_dictionaries(data: List[dict], required_keys: List[str]) -> bool:
    if not data:
        return False
    return all([key in item for item in data] for key in required_keys)


# Select out (clean) a set of keys from an existing dictionary
def select_dictionary_keys(old: dict, select_keys: List[Any]) -> dict:
    return {sel: old[sel] for sel in select_keys}


# Query if a dictionary has a list of required keys
def contains_required_keys(data: dict, required_keys: List[Any]) -> bool:
    return all(req in data for req in required_keys)


# Grab the list of adjustable parameters from a disease file
def list_adjustable_parameters(data: Disease) -> List[str]:
    d_data: dict = asdict(data)
    adjustable_vars: List[str] = []
    for key in list(d_data.keys()):
        if key.startswith('_'):
            continue
        try:
            iter(d_data[key])
            adjustable_vars.append(key)
        except TypeError:
            continue
    return adjustable_vars


# Re-use the metawards code to load the disease from the MetaWardsData if possible
def load_disease_model(file_name: str, data_env: str) -> Disease:
    # Try to get it from an installed MetaWardsData clone, otherwise search for a local copy
    # NOTE: If there *is* a local copy, it will take precedence over the data repo clone!
    d_name, d_ext = os.path.splitext(file_name)
    if not d_name:
        raise ValueError("Invalid file name provided")
    if not d_ext:
        d_ext = ".json"
    mw_data = os.getenv(data_env, "")
    if not mw_data:
        # if we get here, metawards is potentially using a rouge dataset!
        disease_data: Disease = Disease.load("", None, "", d_name + d_ext)
    else:
        disease_data: Disease = Disease.load(d_name, mw_data, "diseases", None)
    return disease_data


# Convert epidemiological parameters to disease variables
# TODO: This could be vectorised (by using numpy.ndarray), but I doubt it is worth it
def transform_epidemiological_to_disease(incubation, infect_time, r_zero) -> (float, float, float, float, float):
    # TODO: Check these validations are correct
    if not incubation > 0.0:
        raise ValueError("Invalid incubation time")
    if not infect_time > 0.0:
        raise ValueError("Invalid infectious period")
    if r_zero < 0.0:
        raise ValueError("Invalid R0")

    beta = r_zero / infect_time
    inv_incu = 1.0 / incubation
    inv_inf = 1.0 / infect_time
    # Quadratic parameters for dt
    quad_a = (beta * inv_incu) - (inv_inf * inv_incu)
    quad_b = inv_inf + inv_incu
    quad_c = -1.0
    disc = np.sqrt((quad_b ** 2) - (4.0 * quad_a * quad_c))
    dt = np.log(2.0) * (((-beta) + disc) / (2.0 * quad_a))
    # Split infection periods
    ip1 = 1.0
    ip2 = infect_time - ip1
    return beta, beta, inv_incu, 1.0 / ip1, 1.0 / ip2


# Output a dictionary to a json file and manage some common exceptions
def export_dictionary_to_json(data: dict, file_name: str):
    if not data:
        raise ValueError("Trying to export empty or invalid dictionary")
    if not file_name:
        raise ValueError("No file name supplied")
    try:
        with open(file_name, "w") as file:
            js.dump(data, file, indent=4, sort_keys=True)
    except OSError as error:
        print("Error saving: " + error.filename)
        raise ValueError("Invalid file name or couldn't write to file")
    except js.JSONDecodeError as error:
        print("JSON Error: " + error.msg)
        raise ValueError("Invalid JSON format")