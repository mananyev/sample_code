"""File :file:`basic_preparation_dataframe.py` contains functions for
preparations of Data Frame:

    - loading data from the *.txt* file with subjects' data,
    - plotting graphs with contributions / beliefs patterns,
    - plotting p-values of tests for the differences between corresponding bars,
    - slicing data in dataframe,
    - computing statistics (e.g. means, stds, median) along certain dimensions,
    - reshaping the data along certain dimensions.
"""


import pandas
import numpy as np
import matplotlib.pyplot as plt
from bld.project_paths import project_paths_join as ppj


def pilot_sessions(project):
    """Returns data frame *rd* read from the CSV file with generated:

        - indicators for sequential game --- *sequential_game*,
        - group composition --- *Group_Composition*,
        - unique subject IDs --- *subject_id*.

    The function requires to be called with a subproject specification
    as the argument in *project*.
    """

    assert project, "Required project name: 'LBE' or 'ELBE'."

    # path to session files
    # (this file is manually created using zTree separation of tables!)
    datafile = "subjects_{}.txt".format(project)

    abs_file_path = ppj('IN_DATA', datafile)

    rd = pandas.read_csv(abs_file_path, sep='\t')

    if project == "LBE":
        rd['sequential_game'] = rd['SessionID'].map({
            '170708_1018': 1,
            '170710_0841': 0,
            '170710_1034': 1,
            '170710_1251': 0
        })
        rd['Group_Composition'] = rd['SessionID'].map({
            "170708_1018": 'HHL',
            "170710_0841": 'HHL',
            "170710_1034": 'LHL',
            "170710_1251": 'LHL'
        })
    elif project == "ELBE":
        rd['sequential_game'] = rd['TreatmentNumber'].map({
            2: 1,
            1: 0
        })
        rd['Group_Composition'] = rd['leader_type'].map({
            2: 'HHL',
            1: 'LHL'
        })
        # THIS IS AN ARTIFACT FROM RAFAEL'S ZTREE FILES: 'type' was overwritten!
        rd['player_type'] = rd['roleorder'].map({
            3: 1,
            2: 2
        }).fillna(rd['leader_type'])
    else:
        raise ValueError("Incorrect project name, required: 'LBE' or 'ELBE'")

    rd['subject_id'] = 0
    for s, session in enumerate(rd['SessionID'].unique()):
        for subject in rd.loc[(rd['SessionID'] == session)]['Subject'].unique():
            rd.loc[
                (rd['SessionID'] == session) & (rd['Subject'] == subject),
                'subject_id'
            ] = s*100 + subject

    # Compute only payoffs from PG (not from correct guessing of beliefs!)
    # Corresponds to ProfitPG in one-shot game and Profit in repeated game
    rd['payoff'] = rd['ProfitPG'].combine_first(rd['Profit'])

    return rd


def plot_pattern(
    project,
    s1,
    s2,
    fig_name,
    fig_title="",
    s1_label="",
    s2_label="",
    pattern="",
    beliefs=0
):
    """Plots DataFrame with averaged CCs contained in *s1* and *s2* and
    saves into the file *fig_name* with optional title *fig_title* and
    axis labels *s1_label* and *s2_label*:

        - with or without respective norms (*pattern* = {"", "L", "H"}),
        - with pre-defined styles.

    The function requires to be called with a subproject specification
    as the argument in *project*.
    Special argument for beliefs = -1 to label y-axis with
    "beliefs of followers".
    """

    assert project, "Required project name: 'LBE' or 'ELBE'."
    assert len(s1) > 0, "Need s1!"
    assert len(s2) > 0, "Need s2!"
    assert len(s1) == len(s2), "s1 and s2 should be of the same length"
    assert fig_name, \
        "Need to provide the name of the file for the figure to be saved to"
    x = np.arange(len(s1))

    graph = plt.figure()
    plt.subplot(111)
    plt.plot(x, s1, 'ko-', label=s1_label)
    plt.plot(x, s2, 'k^-', fillstyle='none', label=s2_label)
    plt.xlabel('Contribution of the leader')
    if beliefs == 0:
        plt.ylabel('Contributions of followers')
    elif beliefs == -1:
        plt.ylabel('Beliefs of followers')
    else:
        plt.ylabel('Contributions / Beliefs')
    plt.axis('scaled')
    plt.xlim(-1, 21)
    plt.xticks(np.arange(0, 21, 2))
    plt.ylim(-1, 21)
    plt.yticks(np.arange(0, 21, 2))
    # plot patterns (Eq Payoff, Eq Contribs, Prop to Returns)
    if pattern == "Lf":
        plt.plot(x, x, '--k', label="$45^\circ$ (L matches L-leader)")
        plt.plot(x, 2*x/5, ':k', label="Equal payoffs wrt H-leader")
        plt.plot(x, 2*x/3, '-.k', label="Proportional to return wrt H-leader")
    elif pattern == "Hf":
        plt.plot(
            x,
            np.minimum(x*2, 20*np.ones(x.shape)),
            ':k',
            label="Equal payoffs wrt L-leader"
        )
        plt.plot(x, x, '--k', label="$45^\circ$ (H matches H-leader)")
        plt.plot(
            x,
            np.minimum(x*1.5, 20*np.ones(x.shape)),
            '-.k',
            label="Proportional to return wrt L-leader"
        )
    elif pattern == "Hl":
        plt.plot(x, x, '--k', label="$45^\circ$ (H matches H-leader)")
        plt.plot(x, 2*x/5, ':k', label="Equal payoffs, L-follower")
        plt.plot(x, 2*x/3, '-.k', label="Proportional to return, L-follower")
    elif pattern == "Ll":
        plt.plot(
            x,
            np.minimum(x*2, 20*np.ones(x.shape)),
            ':k',
            label="Equal payoffs, H-follower"
        )
        plt.plot(x, x, '--k', label="$45^\circ$ (L matches L-leader)")
        plt.plot(
            x,
            np.minimum(x*1.5, 20*np.ones(x.shape)),
            '-.k',
            label="Proportional to return, H-follower"
        )
    else:
        if pattern != "":
            raise ValueError("Should provide either empty (string) pattern, \
                or 'Lf', 'Hf', 'Ll', or 'Hl'!")
    plt.legend(loc=2)
    plt.title(fig_title, fontsize="x-large")
    # graph.tight_layout()  # an alternative to `bbox_inches' below
    graph.savefig(ppj('OUT_FIGURES', project, fig_name), bbox_inches='tight')


def label_diff(ax, text, df, row, columns, extra_space=0):
    """Puts labels with p-values on the bar graph in axis *ax*,
    plotted based on values from data frame *df*.
    *df* must have index *row* and list of columns *columns*.
    The label is plotted with text *text* for differences between
    columns *columns* for a corresponding *row*, and shifted vertically by
    *extra_space*.

    For graphs on slides.
    """

    try:
        Y1 = df.xs(row)[columns[0]]
        Y2 = df.xs(row)[columns[1]]
        X1 = df.index.get_loc(row) \
            + (df.columns.get_loc(columns[0]) \
                - (df.shape[1]-1)/2) / (df.shape[1]*2)
        X2 = df.index.get_loc(row) \
            + (df.columns.get_loc(columns[1]) \
                - (df.shape[1]-1)/2) / (df.shape[1]*2)

        x = (X1+X2) / 2
        y = max(Y1, Y2) + 1 + extra_space

        props = {'connectionstyle': 'bar', 'arrowstyle': '-', 'lw': 2}
        ax.annotate(text, xy=(x, 1.1*y), ha='center')
        ax.annotate('', xy=(X2, y), xytext=(X1, y), arrowprops=props)
    except KeyError:
        print("No such row / column")


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Function for selection of data slice
def slicing(
        df,
        slice,
        from_level,
        columns,
        sort_by=[],
        new_index=[],
        restrict=""
):
    """Returns DataFrame - slice of the data from DataFrame *df* with index
    *new_index* (if *new_index* is empty, sets initial index as *from_level*),
    with columns *columns*, and according to the following restrictions:

        - *slice* values in *from_level*
        - sorted by *sort_by*,
        - truncated by query *restrict*.
    """

    if not restrict:
        restricted = df
    else:
        try:
            restricted = df.query(restrict).dropna(axis=0, how='all')
        except:
            print("Something went wrong with restricting data frame: " \
                + "cannot restrict dataframe with query {}".format(restrict)
            )
            raise
    if not sort_by:
        sorted = restricted.set_index(from_level)
    else:
        try:
            sorted = restricted.set_index(from_level).sort_values(sort_by)
        except:
            print("Cannot sort by these columns: {}".format(sort_by))
            raise
    try:
        sliced = sorted.xs(slice, level=from_level)
    except:
        print("No such values {} in level {}".format(slice, from_level))
        raise
    if not new_index:
        indexed = sliced[columns]
    else:
        try:
            indexed = sliced.reset_index()[columns].set_index(new_index)
        except:
            print("Cannot select columns {}; cannot set index {}".format(
                columns,
                new_index
            ))
    return indexed


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Function for computation of outcomes for summary statistics and graphs
def summarize(
        df,
        column,
        condition=[],
        grouping=[],
        fun="mean"
):
    """Returns DataFrame --- function *fun* over column *column* of the data
    (default: *mean*) from DataFrame *df* truncated by query *condition*,
    grouped by *grouping*.
    """

    if not condition:
        restricted = df
    else:
        try:
            restricted = df.query(condition)
        except:
            print("Something went wrong with restricting data frame: " \
                + "cannot restrict dataframe with query {}".format(condition)
            )
            raise

    if not grouping:
        grouped = restricted
    else:
        try:
            grouped = restricted.groupby(grouping)
        except:
            print("Cannot group by {}".format(grouping))
            raise

    try:
        found = grouped[column]
    except:
        print("Cannot select column {}".format(column))
        raise

    if fun.lower() == "mean":
        statistic = found.mean()
    elif fun.lower() == "std":
        statistic = found.std()
    elif fun.lower() == "min":
        statistic = found.min()
    elif fun.lower() == "max":
        statistic = found.max()
    elif fun.lower() == "count":
        statistic = found.count()
    elif fun.lower() == "median":
        statistic = found.median()
    else:
        print("No such function available: {}".format(fun))
        return False

    return pandas.DataFrame(statistic)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Function for reshaping dataframe
def reshape(
        df1,
        type_n_roles=0,
        unstack_level=0,
        df2=[],
        columns=[],
        new_columns=[],
        multiindex=0,
        new_index=[]
):
    """Returns DataFrame --- reshaped DataFrame *df1* (unstacked at level
    *unstack_level*, default is *new_type* column, see below) with
    replaced types (*new_type*), according to *type_n_roles*:

        - to ['Low type', 'High type'], if *type_n_roles* == 0
          (*new_type* = 'type');
        - to ['Leader', 'L-follower', 'H-follower'], otherwise
          (*new_type* = 'f_type').

    If *df2* is passed, concatenates *df1* and *df2[columns]* with the new name
    *new_columns*. If *multiindex* == 1, resets it to level 1 values.
    Optionally, can provide list of columns names in *new_index*
    to be set as new index.
    """

    # HAVE TO do this way: the truth value of non-empty DataFrame is ambiguous!
    if len(df2) != 0:
        assert columns, "'columns' argument required, empty provided"
        assert new_columns, "'new_columns' argument required, empty provided"
        try:
            df1['column_from_df2'] = df2[columns]
        except:
            print("No such column(s) in df2: {}".format(columns))
            raise
        try:
            df1.columns = new_columns
        except:
            print("Cannot assign column names {} to dataframe df1.\n".format(
                new_columns
            ))
            print("Dataframe df1 has columns {}".format(df1.columns.values))
            raise

    df = df1.reset_index()

    if type_n_roles == 0:
        if 'type' in df.columns:
            new_type = 'type'
        elif 'player_type' in df.columns:
            new_type = 'player_type'
        else:
            raise NameError
        try:
            df[new_type] = df[new_type].map({
                1: "Low type",
                2: "High type"
            })
        except:
            print("No such a column: {}".format(new_type))
            raise
    else:
        new_type = 'f_type'
        if 'type' in df.columns:
            old_type = 'type'
        elif 'player_type' in df.columns:
            old_type = 'player_type'
        else:
            raise NameError
        try:
            df[new_type] = df.where(
                df['role'] == 2,
                0
            )[old_type]
        except:
            print("Either:\n")
            print("\t - no such columns: 'type' or 'role', or\n")
            print("\t - no such role == 2")
            print
            raise
        try:
            df[new_type] = df[new_type].map({
                0: "Leader",
                1: "L-follower",
                2: "H-follower"
            })
            df = df.drop([old_type, 'role'], 1)
        except:
            print("No values: 0, 1, 2 in players' types")
            raise

    if new_index:
        assert new_type in new_index, \
            "New index must contain {}".format(new_type)
        try:
            df = df.set_index(new_index)
        except:
            print("Cannot set index to: '{}'".format(new_index))
            raise
    else:
        try:
            df = df.set_index(['Group_Composition', new_type])
        except:
            print("No such column: 'Group_Composition'")
            raise

    if len(df2) != 0:
        df = df.stack()

    if unstack_level == 0:
        output = df.unstack(new_type)
    else:
        output = df.unstack(unstack_level)

    if multiindex == 1:
        output.columns = output.columns.droplevel(0)
        output = output.rename_axis(None, axis=1)

    return output
