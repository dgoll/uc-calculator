# src/uc_calculator/clean.py
"""Import, merge and clean FRS data

TODO
----
- Data on tenure from household table?
- Why are there so many missing rent observations?
- Data on childcare costs (childcare)
"""
from pathlib import Path

import pandas as pd

COMMON_RENAME = {
    "SERNUM": "id_hh",
    "BENUNIT": "id_bu",
    "PERSON": "id_person",
    "GVTREGNO": "region",
    "GROSS4": "grossing_factor",
}

BU_RENAME = {
    "SERNUM": "id_hh",
    "BENUNIT": "id_bu",
    "PERSON": "id_person",
    "GVTREGNO": "region",
    "ADULTB": "num_adults",
    "BURENT": "rent",
    "BUUC": "uc",
    "DISCBUA1": "num_disabled_adults_core",
    "DISCBUC1": "num_disabled_kids_core",
    "DISWBUA1": "num_disabled_adults_wide",
    "DISWBUC1": "num_disabled_kids_wide",
    "FAMTYPBU": "family_type",
    "KID04": "num_kids_0_to_4",
    "KID510": "num_kids_5_to_10",
    "KID1115": "num_kids_11_to_15",
    "KID1619": "num_kids_16_to_19",
}
BU_RENAME.update(COMMON_RENAME)

ADULT_RENAME = {
    "NINEARNS": "net_income_emp",
    "NINSEIN2": "net_income_self_emp",
    "NININV": "net_income_inv",
    "NINPENIN": "net_income_pen",
    "NINRINC": "net_income_rem",
}
ADULT_RENAME.update(COMMON_RENAME)


def prepare_frs_data():
    frs_raw = import_frs()
    frs_clean = clean_frs(frs_raw)
    # frs_merge = merge_frs(frs_clean)
    # frs_canonical = generate_features_frs(frs_merge)
    return frs_clean


def import_frs():
    raw_table_names = ["adult", "benunit", "chldcare"]
    keys = ["adult", "bu", "childcare"]
    return {
        key: pd.read_spss(Path(f"data/raw/{table}.sav"))
        for key, table in zip(keys, raw_table_names)
    }


def clean_frs(frs_raw):
    adult = clean_adult(frs_raw["adult"])
    bu = clean_bu(frs_raw["bu"])
    # childcare = clean_childcare(childcare_raw)
    return {"adult": adult, "bu": bu}


def clean_adult(adult_raw: pd.DataFrame) -> pd.DataFrame:
    adult = (
        adult_raw.filter(ADULT_RENAME)
        .rename(ADULT_RENAME, axis=1)
        .set_index(["id_hh", "id_bu", "id_person"])
        .assign(
            post_tax_income=lambda x: x.loc[
                :, x.columns.str.startswith("net_income_")
            ].apply(sum, 1)
        )
        .loc[:, ["post_tax_income"]]
    )
    adult.to_parquet(Path("data/interim/adult.parquet"))
    return adult


def clean_bu(bu_raw: pd.DataFrame) -> pd.DataFrame:
    family_types_to_drop = ["Pensioner couple", "Pensioner single"]
    clean_columns_to_keep = ["couple", "rent", "num_kids", "num_adults"]
    bu = (
        bu_raw.filter(BU_RENAME)
        .rename(BU_RENAME, axis=1)
        .set_index(["id_hh", "id_bu"])
        .assign(
            couple=lambda x: x["num_adults"] >= 2,
            num_kids=lambda x: x["num_kids_0_to_4"]
            + x["num_kids_5_to_10"]
            + x["num_kids_11_to_15"]
            + x["num_kids_16_to_19"],
        )
        .loc[
            lambda x: ~x["family_type"].isin(family_types_to_drop),
            clean_columns_to_keep,
        ]
    )
    bu.to_parquet(Path("data/interim/bu.parquet"))
    return bu


if __name__ == "__main__":
    frs_clean = prepare_frs_data()
