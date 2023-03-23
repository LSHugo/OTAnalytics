# % Import libraries and modules
from pathlib import Path

import holoviews as hv
import numpy as np
import pandas as pd
import plotly.express as px
from matplotlib import pyplot as plt
from mpl_chord_diagram import chord_diagram
from plugin_prototypes.zeitbedarfe.otanalytics_parser import (
    JsonParser,
    PandasDataFrameParser,
)

hv.extension("bokeh")


# % set env parameters and path
EVENTS = "event_list"
SECTIONS = "sections"
TIME_FORMAT = "%d.%m%.%y %H:%M Uhr"
eventlist_json_path = Path("data/eventlist.json")
sectionlist_json_path = Path("data/sectionlist.json")
from_time = ""
to_time = ""
interval_length = 2  # im minutes

# % Import Eventlist
eventlist_dict = JsonParser.from_dict(eventlist_json_path)

# % Import Sectionlist
sectionlist_dict = JsonParser.from_dict(sectionlist_json_path)

# % Create DataFrames for meta data and events
events_df = PandasDataFrameParser.from_dict(eventlist_dict[EVENTS]).sort_values(
    ["frame_number"]
)
events_df["timestamp"] = pd.to_datetime(
    events_df["timestamp"], format="%Y-%m-%d_%H-%M-%S"
)

# % Create list of section dicts
sections_dict = sectionlist_dict[SECTIONS]


# % Add degrees to directions
def get_degrees(p_1_x: float, p_1_y: float, p_2_x: float, p_2_y: float) -> float:
    diff_x = p_2_x - p_1_x
    diff_y = p_2_y - p_1_y

    v = np.array([diff_x, diff_y])
    u = np.array([0, -1])

    angle = np.degrees(np.arctan2(np.linalg.det([u, v]), np.dot(u, v)))

    return angle


def deg_range(angle: float) -> float:
    if angle < 0:
        return angle + 360
    elif angle > 360:
        return angle - 360
    else:
        return angle


for s in sections_dict.keys():
    p_1_x = sections_dict[s]["coordinates"]["p_1"]["x"]
    p_1_y = sections_dict[s]["coordinates"]["p_1"]["y"]
    p_2_x = sections_dict[s]["coordinates"]["p_2"]["x"]
    p_2_y = sections_dict[s]["coordinates"]["p_2"]["y"]
    angle = get_degrees(p_1_x, p_1_y, p_2_x, p_2_y)

    if angle == 0:
        angle2 = angle + 360
    else:
        angle2 = angle

    sections_dict[s]["degrees"] = {
        "p1_to_p2": [deg_range(angle - 180), deg_range(angle2)],
        "p2_to_p1": [deg_range(angle), deg_range(angle + 180)],
    }


# % Get direciton names
def get_dir_name_line(event: pd.DataFrame, sections: dict) -> pd.Series:
    section_id = str(event["section_id"])
    section = sections[section_id]

    p_1_x = event["direction_vector"][0]
    p_1_y = event["direction_vector"][1]
    p_2_x = event["event_coordinate"][0]
    p_2_y = event["event_coordinate"][1]

    angle_of_track = deg_range(get_degrees(p_1_x, p_1_y, p_2_x, p_2_y))

    event["angle"] = angle_of_track

    for d in section["directions"].keys():
        min_angle = section["degrees"][d][0]
        max_angle = section["degrees"][d][1]
        if angle_of_track >= min_angle and angle_of_track <= max_angle:
            event["direction"] = section["directions"][d]
            return event
        elif (
            max_angle < min_angle
            and angle_of_track >= min_angle
            and angle_of_track <= 360
        ):
            event["direction"] = section["directions"][d]
            return event
        elif (
            max_angle < min_angle
            and angle_of_track >= 0
            and angle_of_track <= max_angle
        ):
            event["direction"] = section["directions"][d]
            return event


events_df_dir = events_df.apply(get_dir_name_line, args=[sections_dict], axis=1)

# % Create section name mapper
section_name_mapper = {
    sections_dict[s]["section_id"]: sections_dict[s]["name"]
    for s in sections_dict.keys()
}

# % TODO: Set time intervals
if from_time != "":
    from_time_formatted = pd.to_datetime(from_time)
    events_df_dir = events_df_dir[events_df_dir["timestamp"] >= from_time_formatted]
    start_time = from_time_formatted
else:
    start_time = events_df_dir.loc[0, "timestamp"]

if to_time != "":
    to_time_formatted = pd.to_datetime(to_time)
    events_df_dir = events_df_dir[events_df_dir["timestamp"] < to_time_formatted]
else:
    end_time = events_df_dir.loc[len(events_df_dir) - 1, "timestamp"]

duration = end_time - start_time
interval = pd.Timedelta(interval_length, "m")

# % Create counting table
counts_section = (
    events_df_dir.groupby(
        [
            pd.Grouper(key="timestamp", freq=f"{interval_length}Min"),
            "section_id",
            "direction",
            "vehicle_type",
        ]
    )["vehicle_id"]
    .count()
    .reset_index()
    .rename({"timestamp": "time_interval", "vehicle_id": "n_vehicles"}, axis=1)
)
counts_section["section_name"] = counts_section["section_id"].map(section_name_mapper)
counts_section_agg = (
    counts_section.pivot(
        index=["time_interval", "section_id", "section_name", "direction"],
        columns="vehicle_type",
        values="n_vehicles",
    )
    .reset_index()
    .fillna(0)
)


def _set_time_format(series: pd.Series, format: str) -> pd.Series:
    return series.map(lambda x: x.strftime(format))


counts_section["time_interval"] = _set_time_format(
    counts_section["time_interval"], TIME_FORMAT
)
counts_section_agg["time_interval"] = _set_time_format(
    counts_section_agg["time_interval"], TIME_FORMAT
)

# % Create counting plot
fig = px.bar(
    counts_section,
    x="time_interval",
    y="n_vehicles",
    color="vehicle_type",
    barmode="stack",
    facet_col="direction",
    facet_row="section_name",
    facet_col_spacing=0.05,
    facet_row_spacing=0.1,
    height=800,
)

"""fig.update_yaxes(
    title_text="Number of road users",
)"""
fig.update_layout(
    title="Counts at section X",
    xaxis_title="Time of day",
    legend_title="Type of<br>road user",
)
fig.show()

# % Create flow table
flows_section = events_df_dir[["vehicle_id", "vehicle_type", "timestamp", "section_id"]]
flows_section["section_id2"] = flows_section["section_id"]
flows_section = (
    flows_section.pivot_table(
        index="vehicle_id",
        values=["section_id", "section_id2", "timestamp", "vehicle_type"],
        aggfunc={
            "section_id": "first",
            "section_id2": "last",
            "timestamp": "first",
            "vehicle_type": "first",
        },
        fill_value=0,
    )
    .reset_index()
    .rename({"section_id": "from_section", "section_id2": "to_section"}, axis=1)
)
flows_section = (
    flows_section.groupby(
        [
            pd.Grouper(key="timestamp", freq=f"{interval_length}Min"),
            "from_section",
            "to_section",
            "vehicle_type",
        ]
    )["vehicle_id"]
    .count()
    .reset_index()
    .rename({"timestamp": "time_interval"}, axis=1)
)
flows_section["from_section"] = flows_section["from_section"].map(section_name_mapper)
flows_section["to_section"] = flows_section["to_section"].map(section_name_mapper)
flows_section = (
    flows_section.pivot(
        index=["time_interval", "from_section", "to_section"],
        columns="vehicle_type",
        values="vehicle_id",
    )
    .reset_index()
    .fillna(0)
)


# % Create plot of flows
def _get_all_flows_from_sections(
    flows: pd.DataFrame, nodes: pd.DataFrame
) -> pd.DataFrame:
    all_flows = pd.DataFrame()
    all_flows_time = pd.DataFrame()
    for i in nodes["name"]:
        from_section = [i] * len(nodes["name"])
        to_section = list(nodes["name"])
        flows_to_add = pd.DataFrame(
            {"from_section": from_section, "to_section": to_section}
        )
        all_flows = pd.concat([all_flows, flows_to_add])

    for j in flows["time_interval"].unique():
        flows_time_to_add = all_flows
        flows_time_to_add["time_interval"] = j
        all_flows_time = pd.concat([all_flows_time, flows_time_to_add])

    return pd.merge(
        all_flows_time,
        flows,
        on=["from_section", "to_section", "time_interval"],
        how="left",
    ).fillna(0)


nodes = pd.DataFrame(sections_dict).transpose()[["section_id", "name"]]
flows = _get_all_flows_from_sections(flows_section, nodes)


time_intervals = flows_section["time_interval"].unique()
vehicle_types = events_df_dir["vehicle_type"].unique()

fig, axs = plt.subplots(
    len(time_intervals),
    len(vehicle_types),
    dpi=300,
    figsize=(5 * len(time_intervals), 5 * len(vehicle_types)),
)
for i in range(0, len(time_intervals)):
    for j in range(0, len(vehicle_types)):
        if len(vehicle_types) > 1 and len(time_intervals) > 1:
            axs_ij = axs[i, j]
        elif len(vehicle_types) > 1 and len(time_intervals) == 1:
            axs_ij = axs[j]
        elif len(vehicle_types) == 1 and len(time_intervals) > 1:
            axs_ij = axs[i]
        flow_matrix = pd.pivot_table(
            flows[flows["time_interval"] == time_intervals[i]],
            index="from_section",
            columns="to_section",
            values=vehicle_types[j],
            aggfunc="sum",
        ).to_numpy(na_value=0)

        chord_diagram(
            flow_matrix,
            names=nodes["name"],
            order=None,
            width=0.05,
            pad=30.0,
            gap=0.03,
            chordwidth=0.7,
            ax=axs_ij,
            colors=None,
            cmap=None,
            alpha=0.6,
            use_gradient=False,
            chord_colors=None,
            start_at=45,
            extent=360,
            directed=True,
            show=False,
        )
        times = _set_time_format(pd.Series(time_intervals), TIME_FORMAT)
        axs_ij.set_title(
            f"Time Interval: {times[i]},\nRoad User: {vehicle_types[j]}", loc="Left"
        )
