# tests/test_uc_funcs.py
"""Tests for functions calculating universal credit eligibility

TODO
----
- Add docstrings

"""
import numpy as np
import pandas as pd
import pytest

from uc_calculator.uc_funcs import (
    _calculate_child_element,
    _calculate_childcare_element,
    _calculate_disregard,
    _calculate_housing_element,
    _calculate_standard_allowance,
    generate_allowance_and_deduction_df,
    generate_allowance_df,
    generate_uc_df,
)

SEED = 291289
RNG = np.random.default_rng(SEED)


@pytest.fixture(name="data")
def fixture_data():
    n_row = 1000
    bools = [False, True]
    data = pd.DataFrame(index=range(n_row))
    data = data.assign(
        couple=RNG.choice(a=bools, size=n_row, p=[0.5, 0.5]),
        adults_under_25=RNG.choice(a=bools, size=n_row, p=[0.8, 0.2]),
        num_kids=(RNG.choice(a=[0, 1, 2, 3], size=n_row, p=[0.3, 0.3, 0.2, 0.2])),
        childcare_costs=(
            lambda x: (x["num_kids"] > 0) * RNG.uniform(0.0, 2000.0, size=n_row)
        ),
        post_tax_hh_income=RNG.uniform(0.0, 2000.0, size=n_row),
        rent=RNG.uniform(0.0, 2000.0, size=n_row),
    )
    return data


@pytest.fixture(name="params")
def fixture_params():
    parameter_min_max = {
        "standard_single_over_25": (0.0, 600.0),
        "standard_single_under_25": (0.0, 600.0),
        "standard_couple_over_25": (0.0, 600.0),
        "standard_couple_under_25": (0.0, 600.0),
        "child_first": (0.0, 400.0),
        "child_second": (0.0, 400.0),
        "childcare_max_one": (0.0, 700.0),
        "childcare_max_two": (700.0, 1400.0),
        "childcare_prop": (0.0, 1.0),
        "taper": (0.1, 0.8),
        "disregard_kids_no_housing": (0.0, 600.0),
        "disregard_kids_with_housing": (0.0, 600.0),
    }
    return {
        parameter: RNG.uniform(*min_max)
        for parameter, min_max in parameter_min_max.items()
    }


@pytest.mark.parametrize(
    "element_func",
    [
        _calculate_child_element,
        _calculate_childcare_element,
        _calculate_housing_element,
        _calculate_standard_allowance,
    ],
)
def test_calc_weak_positive(element_func, data, params):
    """Test for all standard allowance values being positive and non-missing"""
    output = element_func(data, params)
    assert all(output >= 0.0)


@pytest.mark.parametrize(
    "element_func",
    [
        _calculate_standard_allowance,
        _calculate_child_element,
        _calculate_childcare_element,
        _calculate_housing_element,
    ],
)
def test_calc_non_missing(element_func, data, params):
    """Test for all standard allowance values being positive and non-missing"""
    output = element_func(data, params)
    assert all(output.notna())


class TestStandardAllowance:
    @pytest.mark.parametrize(
        "data_dict, family_type",
        [
            ({"couple": False, "adults_under_25": False}, "standard_single_over_25"),
            ({"couple": False, "adults_under_25": True}, "standard_single_under_25"),
            ({"couple": True, "adults_under_25": False}, "standard_couple_over_25"),
            ({"couple": True, "adults_under_25": True}, "standard_couple_under_25"),
        ],
    )
    def test_family_types(self, data_dict, family_type, params):
        data = pd.DataFrame(data_dict, index=[0])
        standard_allowance = _calculate_standard_allowance(data, params).item()
        assert standard_allowance == params[family_type]


class TestChildElement:
    @pytest.mark.parametrize("num_kids", range(6))
    def test_num_kids(self, num_kids, data, params):
        data["num_kids"] = num_kids
        child_element = _calculate_child_element(data, params)
        if num_kids == 0:
            assert all(child_element == 0.0)
        if num_kids == 1:
            assert all(child_element == params["child_first"])
        if num_kids >= 2:
            assert all(
                child_element == (params["child_first"] + params["child_second"])
            )


class TestChildcareElement:
    @pytest.mark.parametrize("num_kids", range(6))
    def test_num_kids(self, num_kids, data, params):
        data["num_kids"] = num_kids
        data["childcare_costs"] = np.inf
        childcare_element = _calculate_childcare_element(data, params)
        if num_kids == 0:
            assert all(childcare_element == 0.0)
        if num_kids == 1:
            assert all(childcare_element == params["childcare_max_one"])
        if num_kids >= 2:
            assert all(childcare_element == params["childcare_max_two"])

    def test_childcare_costs_zero(self, data, params):
        childcare_costs = 0.0
        data["childcare_costs"] = childcare_costs
        data["num_kids"] = 1
        childcare_element = _calculate_childcare_element(data, params)
        assert all(childcare_element == 0.0)

    def test_childcare_costs_positive(self, data, params):
        childcare_costs = 100.0
        data["childcare_costs"] = childcare_costs
        data["num_kids"] = 1
        childcare_element = _calculate_childcare_element(data, params)
        assert all(childcare_element == params["childcare_prop"] * childcare_costs)


class TestDisregard:
    def test_no_kids(self, data, params):
        data["num_kids"] = 0
        allowance_df = generate_allowance_df(data, params)
        assert all(_calculate_disregard(data, params, allowance_df) == 0.0)

    def test_kids_no_housing(self, data, params):
        data["num_kids"] = 1
        data["rent"] = 0.0
        allowance_df = generate_allowance_df(data, params)
        assert all(
            _calculate_disregard(data, params, allowance_df)
            == params["disregard_kids_no_housing"]
        )

    def test_kids_with_housing(self, data, params):
        data["num_kids"] = 1
        data["rent"] = 100.0
        allowance_df = generate_allowance_df(data, params)
        assert all(
            _calculate_disregard(data, params, allowance_df)
            == params["disregard_kids_with_housing"]
        )


class TestDeductionDF:
    def test_no_income(self, data, params):
        data["post_tax_hh_income"] = 0.0
        _, deduction_df = generate_allowance_and_deduction_df(data, params)
        assert all(deduction_df["full_deduction"] == 0.0)

    def test_high_income(self, data, params):
        data["post_tax_hh_income"] = 1e10
        allowance_df, deduction_df = generate_allowance_and_deduction_df(data, params)
        assert all(deduction_df["capped_deduction"] == allowance_df["full_allowance"])

    def test_weakly_positive(self, data, params):
        _, deduction_df = generate_allowance_and_deduction_df(data, params)
        assert all(deduction_df["capped_deduction"] >= 0.0)

    def test_non_missing(self, data, params):
        _, deduction_df = generate_allowance_and_deduction_df(data, params)
        assert all(deduction_df["capped_deduction"].notna())

    def test_capped_less_than_full(self, data, params):
        _, deduction_df = generate_allowance_and_deduction_df(data, params)
        assert all(deduction_df["capped_deduction"] <= deduction_df["full_deduction"])

    def test_weakly_increasing_in_income(self, data, params):
        higher_inc_data = data.assign(
            post_tax_hh_income=lambda x: x.post_tax_hh_income * (1.01)
        )
        _, base_deduction_df = generate_allowance_and_deduction_df(data, params)
        _, higher_inc_deduction_df = generate_allowance_and_deduction_df(
            higher_inc_data, params
        )
        assert all(
            base_deduction_df["capped_deduction"]
            <= higher_inc_deduction_df["full_deduction"]
        )


class TestUCDF:
    def test_no_income(self, data, params):
        data["post_tax_hh_income"] = 0.0
        uc_df = generate_uc_df(data, params)
        assert all(uc_df["uc_receipt"] == uc_df["full_allowance"])

    def test_high_income(self, data, params):
        data["post_tax_hh_income"] = 1e10
        uc_df = generate_uc_df(data, params)
        assert all(uc_df["uc_receipt"] == 0.0)

    def test_weakly_positive(self, data, params):
        uc_df = generate_uc_df(data, params)
        assert all(uc_df["uc_receipt"] >= 0.0)

    def test_non_missing(self, data, params):
        uc_df = generate_uc_df(data, params)
        assert all(uc_df["uc_receipt"].notna())

    def test_weakly_increasing_in_kids(self, data, params):
        more_kids_data = data.assign(num_kids=lambda x: x["num_kids"] + 1)
        base_uc, more_kids_uc = [
            generate_uc_df(df, params) for df in [data, more_kids_data]
        ]
        assert all(more_kids_uc["uc_receipt"] >= base_uc["uc_receipt"])
