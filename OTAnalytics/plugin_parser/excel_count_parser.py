import pandas as pd
from pathlib import Path


class ExcelCountParser:
    
    def __init__(self, path: Path, id_dict: dict, CONFIG: dict):
        self.path = path
        self.id_to_class = id_dict['id_to_class']
        self.id_to_from_section = id_dict['id_to_from_section']
        self.id_to_to_section = id_dict['id_to_to_section']
        self.CONFIG = CONFIG

    def read_excel(self, path: Path) -> pd.DataFrame:
        return pd.DataFrame(data=pd.read_excel(path, sheet_name='Zaehler', skiprows=range(1), usecols=['Klasse','Strom','Zeitstempel']))

    def formatting(self, excel_table: pd.DataFrame) -> pd.DataFrame:

        formatted_table = excel_table

        # Renaming columns to match column names in flow_table
        formatted_table.rename(columns={'Klasse':'road_user_type', 'Zeitstempel':'time_interval'}, inplace=True)

        # Time formatting
        formatted_table['time_interval'] = pd.Timestamp(self.CONFIG['date'] + 'T' + self.CONFIG['from_time']) + pd.to_timedelta(formatted_table['time_interval'], unit='s')

        # Replacing vehicle class IDs by the proper vehicle names
        formatted_table['road_user_type'] = formatted_table['road_user_type'].map(self.id_to_class)

        # Getting sections of origin and destination from "Strom" in two different columns
        formatted_table['from_section'] = formatted_table['Strom'].map(self.id_to_from_section)
        formatted_table['to_section'] = formatted_table['Strom'].map(self.id_to_to_section)

        # Group by sections, time interval, and road user type
        formatted_table = formatted_table.groupby(['from_section','to_section',pd.Grouper(freq=str(self.CONFIG['interval_length_min'])+'min', key='time_interval'),'road_user_type']).count().reset_index()

        return formatted_table

    def excel_parser(self) -> pd.DataFrame:
        return self.formatting(self.read_excel(self.path))