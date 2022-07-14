# src/uc_calculator/clean.py
"""Import, merge and clean FRS data

TODO
----
- Data on post-tax household income (net income variables in adult)
- Data on age of adults (under 25)
- Data on childcare costs (childcare)
"""
from pathlib import Path

import pandas as pd

FRS_RENAME = {
    "SERNUM": "id_household",
    "BENUNIT": "id_ben_unit",
    "PERSON": "id_person",
    "GVTREGNO": "region",
    "ADULTB": "num_adults",
    "BUEARNS": "gross_income_employment",
    "BUINC": "gross_income_all",
    "BUKIDS": "family_type",
    "BURENT": "gross_rent",
    "BUUC": "uc",
    "DISCBUA1": "num_disabled_adults_core",
    "DISCBUC1": "num_disabled_kids_core",
    "DISWBUA1": "num_disabled_adults_wide",
    "DISWBUC1": "num_disabled_kids_wide",
    "FAMTYPBU": "family_type",
    "GROSS4": "grossing_factor",
    "KID04": "num_kids_0_to_4",
    "KID510": "num_kids_5_to_10",
    "KID1115": "num_kids_11_to_15",
    "KID1619": "num_kids_16_to_19",
}


def import_and_clean_frs():
    adult_raw, ben_unit_raw, childcare_raw = import_frs()
    ben_unit = clean_ben_unit(ben_unit_raw)
    return ben_unit


def import_frs():
    adult, ben_unit, childcare = [
        pd.read_spss(Path(f"data/raw/{table}.sav"))
        for table in ["adult", "benunit", "childcare"]
    ]
    return adult, ben_unit, childcare


def clean_ben_unit(ben_unit_raw: pd.DataFrame) -> pd.DataFrame:
    ben_unit = (
        ben_unit_raw.filter(FRS_RENAME, axis=1)
        .rename(FRS_RENAME, axis=1)
        .set_index(["id_household", "id_ben_unit"])
    )
    return ben_unit


if __name__ == "__main__":
    ben_unit_raw = import_and_clean_frs()
