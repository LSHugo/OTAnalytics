import pandas as pd
from pathlib import Path
import plotly.express as px


class ExcelCountParser:
    
    def __init__(self, path_list: list, id_dict: dict, CONFIG: dict):
        self.path_list = path_list
        self.id_to_class = id_dict['id_to_class']
        self.id_to_from_section = id_dict['id_to_from_section']
        self.id_to_to_section = id_dict['id_to_to_section']
        self.CONFIG = CONFIG

    def excel_parser(self) -> pd.DataFrame:

        formatted_table = pd.DataFrame()

        for path in self.path_list:
            
            # Reading and importing the Excel counting sheet 
            new_table = pd.DataFrame(data=pd.read_excel(path, sheet_name='Zaehler', skiprows=range(1), usecols=['Klasse','Strom','Zeitstempel']))
            
            # Getting the starting time from the file's name
            new_table['from_time'] = path[len(self.CONFIG['file_name_prefix']):len(self.CONFIG['file_name_prefix'])+4]
            
            # Concatenating the counting tables of all mentioned files
            formatted_table = pd.concat([formatted_table, new_table])

        # Renaming columns to match column names in flow_table
        formatted_table.rename(columns={'Klasse':'road_user_type', 'Zeitstempel':'time_interval'}, inplace=True)

        # Time formatting
        formatted_table['from_time'] = self.CONFIG['date'] + 'T' + formatted_table['from_time']
        formatted_table['time_interval'] = pd.to_datetime(formatted_table['from_time']) + pd.to_timedelta(formatted_table['time_interval'], unit='s')
        formatted_table = formatted_table.drop(columns=['from_time'])

        # Replacing vehicle class IDs by the proper vehicle names
        formatted_table['road_user_type'] = formatted_table['road_user_type'].map(self.id_to_class)

        # Getting sections of origin and destination from "Strom" in two different columns
        formatted_table['from_section'] = formatted_table['Strom'].map(self.id_to_from_section)
        formatted_table['to_section'] = formatted_table['Strom'].map(self.id_to_to_section)

        # Group by sections, time interval, and road user type
        formatted_table = formatted_table.groupby(['from_section','to_section',pd.Grouper(freq=str(self.CONFIG['interval_length_min'])+'min', key='time_interval'),'road_user_type']).count().reset_index()
        formatted_table.rename(columns={'Strom':'n_vehicles'}, inplace=True)

        return formatted_table
    
    def comparison_table(self, model_flow_table: pd.DataFrame) -> pd.DataFrame:

        excel_flow_table = self.excel_parser()

        # Joining the count tables of the manual count and the model's count
        comparison_table = pd.merge(excel_flow_table, model_flow_table, on=['from_section','to_section','time_interval','road_user_type'], how='outer', suffixes=('_excel','_model'))
        comparison_table.fillna(0, inplace=True)

        # Brut difference
        comparison_table['difference'] = abs(comparison_table['n_vehicles_excel']-comparison_table['n_vehicles_model'])
        
        # Counting ratio (different cases to avoid dividing by 0)
        comparison_table.loc[comparison_table['n_vehicles_model'] != 0, 'counting_ratio'] = comparison_table['n_vehicles_excel']/comparison_table['n_vehicles_model']
        comparison_table.loc[(comparison_table['n_vehicles_excel'] == 0) | (comparison_table['n_vehicles_model'] == 0), 'counting_ratio'] = 0

        return comparison_table

    def count_table(self, model_flow_table: pd.DataFrame) -> pd.DataFrame:
        
        excel_flow_table = self.excel_parser()
        
        excel_flow_table['table'] = 'excel'
        model_flow_table['table'] = 'model'
        
        count_tables = pd.concat([excel_flow_table, model_flow_table])
        count_tables['time_interval'] = count_tables['time_interval'].astype(str)

        return count_tables
    
    def plot_compared_counts(self, model_flow_table: pd.DataFrame):
        
        count_tables = self.count_table(model_flow_table)

        sorted_time_interval = list(set(count_tables['time_interval']))
        sorted_time_interval.sort()

        fig = px.histogram(
            count_tables,
            x='table',
            y='n_vehicles',
            barmode='stack',
            facet_col='time_interval',
            category_orders={'time_interval':sorted_time_interval},
            color="road_user_type",
            nbins=len(set(count_tables['time_interval']))
        )

        fig.update_layout(bargap=0.1)
        fig.show()

    def plot_difference(self, model_flow_table: pd.DataFrame):
    
        comparison_table = self.comparison_table(model_flow_table)

        fig = px.histogram(
        comparison_table,
        x='time_interval',
        y='difference',
        barmode='stack',
        color="road_user_type",
        nbins=len(set(comparison_table['time_interval']))
        )

        fig.update_layout(bargap=0.1)
        fig.show()

    def plot_counting_ratio(self, model_flow_table: pd.DataFrame):

        comparison_table = self.comparison_table(model_flow_table)

        fig = px.histogram(
        comparison_table,
        x='time_interval',
        y='counting_ratio',
        barmode='stack',
        color="road_user_type",
        nbins=len(set(comparison_table['time_interval']))
        )

        fig.update_layout(bargap=0.1)
        fig.show()
    
    def boxplot_per_time_interval(self, model_flow_table: pd.DataFrame, variable_name: str = "counting_ratio"):

        comparison_table = self.comparison_table(model_flow_table)
        comparison_table_non_zero = comparison_table.drop(comparison_table[(comparison_table.n_vehicles_excel == 0) & (comparison_table.n_vehicles_model == 0)].index)
        comparison_table_boxplot = comparison_table_non_zero.groupby(['time_interval','road_user_type'])[variable_name].sum().reset_index()

        fig = px.box(comparison_table_boxplot,x="road_user_type",y=variable_name)
        fig.show()