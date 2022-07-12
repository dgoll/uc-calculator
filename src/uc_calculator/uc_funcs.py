# src/uc_calculator/uc_funcs.py
"""Functions to calculate Universal Credit eligibiliity

TODO
----
- Add disability for child element
- Add grandfathering by DOB for child element
- Add adult disability element
- Add caps to housing element (SAR if under 35 and single, bedroom limit)
- Add assistance for home owners or shared ownership
"""
import numpy as np
import pandas as pd


def generate_uc_df(data: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Generate dataframe containing UC allowances, deductions and receipt

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    pd.DataFrame
        DataFrame containing allowances, deductions and total UC for each BU.
    """
    allowance_df, deduction_df = generate_allowance_and_deduction_df(data, params)
    uc_receipt = _calculate_uc_receipt(allowance_df, deduction_df)
    return pd.concat([allowance_df, deduction_df, uc_receipt], axis=1)


def generate_allowance_and_deduction_df(
    data: pd.DataFrame, params: dict
) -> tuple[pd.DataFrame]:
    """Generate dataframes containing UC allowances and deductions

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    tuple[pd.DataFrame]
        (DataFrame containing allowances for each BU,
        DataFrame containing deductions for each BU)
    """
    allowance_df = generate_allowance_df(data, params)
    deduction_df = generate_deduction_df(data, params, allowance_df)
    return allowance_df, deduction_df


def generate_allowance_df(data: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Generate dataframe containing UC allowances

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    pd.DataFrame
        DataFrame containing allowances for each BU.
    """
    standard = _calculate_standard_allowance(data, params)
    child = _calculate_child_element(data, params)
    childcare = _calculate_childcare_element(data, params)
    housing = _calculate_housing_element(data, params)
    full = pd.Series(standard + child + childcare + housing, name="full_allowance")
    return pd.concat([standard, child, childcare, housing, full], axis=1)


def generate_deduction_df(
    data: pd.DataFrame, params: dict, allowance_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate dataframe containing UC deductions

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs.
    params : dict
        Universal Credit parameters.
    allowance_df : pd.DataFrame
        DataFrame containing allowances for each BU.

    Returns
    -------
    pd.DataFrame
        DataFrame containing deductions for each BU.
    """
    allowance = allowance_df["full_allowance"]
    disregard = _calculate_disregard(data, params, allowance_df)
    deduction = (data["post_tax_hh_income"] - disregard) * params["taper"]
    deduction[deduction < 0.0] = 0.0
    capped_deduction = deduction.mask(deduction >= allowance, allowance)
    deduction_df = pd.concat([disregard, deduction, capped_deduction], axis=1)
    deduction_df.columns = ["disregard", "full_deduction", "capped_deduction"]
    return deduction_df


def _calculate_standard_allowance(data: pd.DataFrame, params: dict) -> pd.Series:
    """Calculate standard allowance amounts for BUs in DataFrame

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs. Must contain
        "couple" (bool) indicating at least two adults in household and
        "adults_under_25" (bool) indicating all adults under age of 25.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    pd.Series
        Standard allowance amounts for each BU.
    """
    family_types = [
        ~data["couple"] & ~data["adults_under_25"],
        ~data["couple"] & data["adults_under_25"],
        data["couple"] & ~data["adults_under_25"],
        data["couple"] & data["adults_under_25"],
    ]
    standard_allowance_params = [
        params["standard_single_over_25"],
        params["standard_single_under_25"],
        params["standard_couple_over_25"],
        params["standard_couple_under_25"],
    ]
    standard_allowance = np.select(family_types, standard_allowance_params)
    return pd.Series(standard_allowance, index=data.index, name="standard_allowance")


def _calculate_child_element(data: pd.DataFrame, params: dict) -> pd.Series:
    """Calculate child element for BUs in DataFrame

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs. Must contain
        "num_kids" (int) counting number of children in BU.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    pd.Series
        Child element for each BU.
    """
    child_element = np.zeros(data.shape[0])
    child_element[data["num_kids"] >= 1] += params["child_first"]
    child_element[data["num_kids"] >= 2] += params["child_second"]
    return pd.Series(child_element, index=data.index, name="child_element")


def _calculate_childcare_element(data: pd.DataFrame, params: dict) -> pd.Series:
    """Calculate childcare element for BUs in DataFrame

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs. Must contain
        "num_kids" (int) counting number of children in BU and
        "childcare_costs" (float) containing total expenditure on childcare.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    pd.Series
        Childcare element for each BU.
    """
    childcare_element = data["childcare_costs"] * params["childcare_prop"]
    childcare_element[data["num_kids"] == 0] = 0.0
    childcare_element[
        (data["num_kids"] == 1) & (childcare_element > params["childcare_max_one"])
    ] = params["childcare_max_one"]
    childcare_element[
        (data["num_kids"] >= 2) & (childcare_element > params["childcare_max_two"])
    ] = params["childcare_max_two"]
    return pd.Series(childcare_element, name="childcare_element")


def _calculate_housing_element(data: pd.DataFrame, params: dict) -> pd.Series:
    """Calculate housing element for BUs in DataFrame

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs. Must contain
        "rent" (float) containing expenditure on rent.
    params : dict
        Universal Credit parameters.

    Returns
    -------
    pd.Series
        Housing element for each BU.
    """
    return pd.Series(data["rent"], name="housing_element")


def _calculate_disregard(
    data: pd.DataFrame, params: dict, allowance_df: pd.DataFrame
) -> pd.Series:
    """Calculate disregard for BUs in DataFrame

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame of BUs. Must contain
        "num_kids" (int) counting number of children in BU.
    params : dict
        Universal Credit parameters.
    allowance_df : pd.DataFrame
        DataFrame containing allowance elements by BU.

    Returns
    -------
    pd.Series
        Disregard for each BU
    """
    family_types = [
        (data["num_kids"] == 0),
        (data["num_kids"] > 0) & (allowance_df["housing_element"] == 0),
        (data["num_kids"] > 0) & (allowance_df["housing_element"] > 0),
    ]
    disregard_parameters = [
        0.0,
        params["disregard_kids_no_housing"],
        params["disregard_kids_with_housing"],
    ]
    disregard = np.select(family_types, disregard_parameters)
    return pd.Series(disregard, index=data.index, name="disregard")


def _calculate_uc_receipt(
    allowance_df: pd.DataFrame, deduction_df: pd.DataFrame
) -> pd.Series:
    """Calculate total universal credit received for BUs in DataFrame

    Parameters
    ----------
    allowance_df : pd.DataFrame
        DataFrame containing allowance elements by BU.
    deduction_df : pd.DataFrame
        DataFrame containing earnings deduction by BU.

    Returns
    -------
    pd.Series
        Universal credit receipt for each BU.
    """
    uc_receipt = allowance_df["full_allowance"] - deduction_df["capped_deduction"]
    return pd.Series(uc_receipt, name="uc_receipt")
