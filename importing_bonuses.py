"""File :file:`importing_bonuses.py` prepares and exports the data on bonuses
from Excel files to temporary STATA files,
loading the data from *data/Excel/*
and placing the results into *bld/out/data/stata/temp/*.

Paths are automatically generated with an imported module :mod:`project_paths`.

Must be called with an argument --- input filename.
"""


# import libraries
import pandas as pd
import numpy as np
import sys

from bld.project_paths import project_paths_join as ppj


class spec_dict(dict):
    """Special class for an 'extended' dictionary that returns
    key name if the value for that key is missing.
    """

    def __missing__(self, key):
        return key


def to_stata_b(filein):
    """Reads a DataFrame, imported from Excel file provided in
    a string argument ``filein`` and saves it in a Stata file
    with the same name.
    Variables are renamed according to the data in the first two rows
    (year and month).
    """

    assert filein, "Must provide a file name"

    # import data
    try:
        rd = pd.read_excel(
            ppj("IN_DATA", "Excel", filein),
            header=None,
            encoding='cp1251'
        )
    except:
        raise

    # 'Translate' the months
    months_ru_en = spec_dict({
        'ID': 'id',
        "январь": "1m",
        "февраль": "2m",
        "март": "3m",
        "апрель": "4m",
        "май": "5m",
        "июнь": "6m",
        "июль": "7m",
        "август": "8m",
        "сентябрь": "9m",
        "октябрь": "10m",
        "ноябрь": "11m",
        "декабрь": "12m",
        "доплаты за досрочное выполнение работ, за срочность работ": "yearly",
    })
    whatisit = {
        "выплаты за сверхурочность, работу в вых и празндничные дни": 0,
        "премия, фиксированный процент от оклада": 1,
    }
    # rename columns
    new_colnames = []
    months = rd.iloc[1].map(months_ru_en)
    years = rd.iloc[0]
    prev_year = ""
    for i in np.arange(len(rd.columns)):
        if months[i] == "id":
            new_colnames.append("id")
            continue
        if (months[i] == "yearly"):
            new_colnames.append("yearly_{}".format(prev_year))
            continue
        if years[i] == \
            "доплаты за досрочное выполнение работ, за срочность работ":
            new_colnames.append("yearly_{}".format(months[i]))
            continue
        year = str(years[i]).replace("год", "").strip()
        new_colnames.append("b_{m}{y}".format(
            m=months[i],
            y=year
        ))
        prev_year = year
    rd.columns = new_colnames
    # create new id from string variables
    pat = r"(?P<one>\d) нов"
    repl = lambda m: m.group('one') + '0000'
    rd["new_id"] = rd["id"].str.replace(pat, repl)
    rd["person_id"] = pd.to_numeric(
        rd["new_id"].combine_first(rd["id"]),
        errors='coerce',
        downcast='integer'
    )
    rd['percent'] = rd['b_nannan'].map(whatisit)
    rd = rd.drop(columns=['id', 'new_id', 'b_nannan'])
    rd = rd.drop([0, 1]).set_index("person_id")

    # # Write CSV file (to check)
    # fileout_csv = filein.split(".")[0].replace("-", "_") + ".csv"
    # rd.to_csv(ppj('DATA_TEMP', fileout_csv))

    # Write STATA file
    fileout_dta = filein.split(".")[0].replace("-", "_") + ".dta"
    rd.astype(float).to_stata(ppj('DATA_TEMP', fileout_dta))



if __name__ == "__main__":
    # Check if the file name provided
    assert len(sys.argv) >= 2, "Must specify the argument - file name."

    filename = sys.argv[1]

    to_stata_b(filein=filename)
