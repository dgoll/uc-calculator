# src/uc_calculator/clean.py
"""Import, merge and clean FRS data

XXXX
"""
from pathlib import Path

import pandas as pd


def import_frs():
    bunit = pd.read_spss(Path("data/raw/benunit.sav"))
    hh = pd.read_spss(Path("data/raw/househol.sav"))
    return bunit, hh


if __name__ == "__main__":
    pass
