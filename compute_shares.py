"""File :file:`compute_shares.py` calculates respective cumulative shares
of wages owed and repaid by the firm in a given month
for each indivudual in each wave.

The file requires to be called without an argument.
"""


import pandas as pd
import numpy as np
import sys

from bld.project_paths import project_paths_join as ppj


def shares():
    """Reads DataFrame from the file :file:`to_compute_shares.dta` located in
    *bld/out/data/Stata/temp/*, calculates shares of repaid wages as follows.
    For a given month, take the amount repaid, check if it is larger than
    the amount owed in the first month of arrears in the current wave.
    If larger - then save the share of arrear that is covered,
    subtract it from repaid amount, and compare what is left
    to the next month's arrear. Repeat for the next month.

    Saves the result in the file :file:`computed_shares.dta` located in
    *bld/out/data/Stata/temp/*.

    .. warning:: the input file (:file:`to_compute_shares.dta`) must contain
    the following columns:

        * id,
        * wave,
        * modate,
        * wage,
        * amount_owed,
        * amount_repaid.
    """

    df = pd.read_stata(ppj('DATA_TEMP', 'to_compute_shares.dta'))

    # What must be in the columns in Stata file:
    # id, wave, modate, wage, amount_owed, amount_repaid
    df = df.set_index(['id', 'wave', 'modate'])
    df["a2w"] = np.nan
    df["cumsum_a2w"] = np.nan
    df["r2w"] = np.nan
    df["r2cw"] = np.nan
    df["cumsum_r2w"] = np.nan
    df["shares"] = np.nan
    df["cumsum_shares"] = np.nan
    df["psy_costs"] = np.nan
    # calculate the wage that was supposed to be paid
    df["supp_wage"] = (
        df["amount_owed"].fillna(0) + df["wage"]
    ).values
    df["a2w"] = (
        df["amount_owed"] / df["supp_wage"]
    ).values
    df["r2cw"] = (
        df["amount_repaid"] / df["supp_wage"]
    ).values
    # Sometimes STATA handles string to numeric conversions very badly
    # In case of problems, check the following line:
    # df["wage"] = np.around(df["wage"]*100).values.astype(int) / 100

    # for each INDIVIDUAL in the sample
    for id in df.reset_index()["id"].unique():
        # for each WAVE individual was working
        for wave in df.loc[id].index.get_level_values('wave').unique():
            df.loc[(id, wave), "cumsum_a2w"] = \
                df.loc[(id, wave)]["a2w"].cumsum().values
            # modate when arrears appear during wave for the first time
            fa_date = df.loc[(id, wave)].dropna(
                subset=["amount_owed"]
            ).index.get_level_values('modate').min()
            # arrear amount in the respective first arrear modate
            if not np.isnan(fa_date):
                fa = df.loc[(id, wave, fa_date)]["amount_owed"]
                # wage in the respective first arrear modate
                fa_wage = df.loc[(id, wave, fa_date)]["supp_wage"]

                # now, for each REPAYMENTS month
                for date in df.loc[(id, wave)].dropna(
                    subset=["amount_repaid"]
                ).index.get_level_values('modate'):
                    # how much was repaid in a given month
                    rest_rep = df.loc[(id, wave, date)]["amount_repaid"]

                    # FIFO repayments:
                    # calculate the shares repaid according to the
                    # "first in, first out" rule.
                    # If in this month repaid more than was amount of arrears
                    # in the first month
                    share_repaid = 0
                    while rest_rep > fa:
                        # how much of the corresponding share we should subtract
                        share_repaid = share_repaid + fa/fa_wage
                        # this is how much more was repaid
                        # (after the first arrear was compensated)
                        rest_rep = rest_rep - fa
                        # take next month
                        # (now, this is the "first" yet uncompensated month)
                        fa_date += 1
                        # take arrear from that month
                        fa = df.loc[(id, wave, fa_date)]["amount_owed"]
                        fa_wage = df.loc[(id, wave, fa_date)]["supp_wage"]
                    share_repaid = share_repaid + rest_rep/fa_wage
                    df.loc[(id, wave, date), "r2w"] = share_repaid
                    # yet unpaid amount from the first arrear
                    fa = fa - rest_rep
            # for each worker and wave:
            df.loc[(id, wave), "cumsum_r2w"] = \
                df.loc[(id, wave)]["r2w"].cumsum().values
            df.loc[(id, wave), "shares"] = (
                df.loc[(id, wave)]["a2w"].fillna(0) \
                - df.loc[(id, wave)]["r2w"].fillna(0)
            ).values
            df.loc[(id, wave), "cumsum_shares"] = \
                df.loc[(id, wave)]["shares"].cumsum().values

        # compute accumulated ``psychological costs'' for each individual
        # (cumulative across ALL waves)
        df.loc[id, "costs"] = (
            df.loc[id]["r2w"].fillna(0) - df.loc[id]["r2cw"].fillna(0)
        ).values
        df.loc[id, "psy_costs"] = \
            df.loc[id]["costs"].cumsum().values

    # if needed in a specific file
    # fileout_dta = filein.split(".")[0].replace("-", "_") + ".dta"
    # save all variables generated in the script
    # (although, need only first four!)
    df[[
        "cumsum_shares",
        "psy_costs",
        "cumsum_a2w",
        "cumsum_r2w",
        "a2w",
        "r2w",
        "r2cw",
        "costs",
        "shares",
    ]].astype(float).to_stata(ppj('DATA_TEMP', 'computed_shares.dta'))



if __name__ == "__main__":
    # run the function (if needed to provide additional arguments in the future)
    shares()
