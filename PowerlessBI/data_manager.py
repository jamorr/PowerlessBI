""""

SPLIT SAVES INTO THEIR OWN FOLDERS WHICH CONTAIN:
    - json containg:
        - path settings
        - type dict
        - operations performed after import
    - hard reference copy of the file
        - always tracks where file is moved to or if deleted
    - parquet if saved to one
Instead of loading jsons - load folder names first
make folder in my documents

"""
import json
import os
import pandas as pd
from tkinter import messagebox
import ast
import pandas.io.parsers.c_parser_wrapper as pandas_type_parser

class DataManager:
    def __init__(self) -> None:
        self.directory = os.getcwd()
        self.settings = self.settings_json()
        self.save_path:str = self.settings['saves_path']
        if os.path.exists(self.save_path):
            self.save_folders = os.listdir(self.save_path)
        else:
            # print("settings path does not exist would you like to set one now?")
            os.mkdir(self.save_path)
            self.save_folders = os.listdir(self.save_path)

    def settings_json(self):
        with open("../settings.json", "r") as f:
            return json.load(f)

    def get_path_settings(self) -> list[str]:
        return self.save_folders


    def parse_inputs(
        self,
        file_loc:str,
        delim:str|None,
        rad_var:int,
        col_names:list[str]|None,
        index_list:list[int]|None,
        data_type:dict[str,str]|None,
        dt_parser_str:list[str]|bool|None,
    ):
        # TODO: implement DT parser
        dt_parser = self.convert_dates(dt_parser_str)
        if dt_parser is None:
            dt_parser = False
        header = 'infer' if rad_var == 1 else 0

        if data_type:
            for dtype in data_type.values():
                try:
                    pandas_type_parser.ensure_dtype_objs(dtype)
                except TypeError:
                    raise TypeError

        settings = {
            name: set for name, set in zip(['filepath_or_buffer', 'dtype',
                                            'names','header', 'sep',
                                            'index_col','parse_dates'],
                                            [file_loc, data_type, col_names, header,
                                            delim, index_list, dt_parser]
                                            )
        }

        print(settings)
        if not settings['dtype']:
            settings['dtype'] = None
        if not settings['index_col']:
            del settings['index_col']
        if not settings['parse_dates']:
            del settings['parse_dates']
        if not settings['names']:
            del settings['names']
        print(settings)

        return settings


    # TODO: converts date strings into correct format
    def convert_dates(self, dates):
        return

    def new_save(self,
                 alias: str,
                 path_settings: dict[str, None | dict | int | list | str],
                 data_types: dict[str, list[str]],
                 operations: list):

        # check if dir exists
        if os.path.exists(self.save_path+alias):
            print("Save already exists.")
            return
        os.mkdir(self.save_path+alias)
        os.mkdir(self.save_path+alias+"/data")
        os.mkdir(self.save_path+alias+"/plots")

        # create json containing path settings, type dict,
        # and operations performed after import
        save_settings = {
            "path_settings": path_settings,
            "data_types": data_types,
            "operations": operations
        }
        with open(self.save_path+alias+"/settings.json", "w") as f:
            json.dump(save_settings, f)

        if os.path.exists(path_settings['filepath_or_buffer']) and \
            path_settings['filepath_or_buffer'] not in \
                os.listdir(f"{self.save_path + alias}/data/"):
            # create hard reference copy of file
            os.system(f"cp {path_settings['filepath_or_buffer']}"
                      f"{self.save_path + alias}/data/")


        # create parquet if file is of supported type
        # if file_type == "csv":
        #     os.system("pandas.read_csv("+file_path+").to_parquet("+self.save_path+alias+"/data/data.parquet")")
        # elif file_type == "xlsx":
        #     os.system("pandas.read_excel("+file_path+").to_parquet("+self.save_path+alias+"/data/data.parquet")")
        # add more file types as needed

    def load_save(self, alias: str):
        if alias not in self.save_folders:
            print("Save not found.")
            return

        with open(self.save_path+alias+"/settings.json", "r") as f:
            settings = json.load(f)

        # load data from parquet if available
        if os.path.exists(self.save_path+alias+"/data/data.parquet"):
            data = pd.read_parquet(self.save_path+alias+"/data/data.parquet")
        else:
            data = pd.read_csv(settings["path"]) if settings["type"] == "csv"\
                else pd.read_excel(settings["path"])

        # apply operations as specified in settings
        for operation in settings["operations"]:
            if operation == "dropna":
                data.dropna(inplace=True)
            # add more operations as needed

        return data

    def save_data_frame(self, settings):
        """ Save pandas DataFrame displayed in table as csv"""
        # get path name and alias/new file name
        path = self.path_text.get()
        if not path:
            messagebox.showerror('ERROR', message='Select a file path')
            return None

        # check if user intends to overwrite existing save
        overwrite = True
        if self.selected.get() != '':
            overwrite = messagebox.askyesnocancel(
                'Warning',
                message='Overwrite the selected path?\n'
                'Select Yes to proceed, No to save without'
                ' overwriting, or Cancel to exit.'
            )

        if overwrite is False:
            self.selected.set('')
        elif overwrite is None:
            return None

        # Check for valid path
        try:
            dirname = os.path.dirname(path)
        except AttributeError or TypeError:
            messagebox.showerror('ERROR', message='Invalid Path')
            return None

        # get alias from path name/input if no alias given
        alias = self.check_alias(self.act_frame.alias_entry.get())
        if alias is None:
            return None

        # get path and set new path
        path = dirname + '/' + alias + '.csv'
        self.act_frame.alias_entry.setvar(path)

        # get settings
        index_name = self.table.model.df.index.name
        settings = {
            'filepath_or_buffer': path,
            'names': None,
            'header': self.last_import['header']
            if self.last_import is not None else 'infer',
            'sep': ",", # figure out how to get separator from df
            'index_col': index_name if index_name is not None else 0,
            'converters': None, 'parse_dates': False
        }

        # save file to path and save path to json
        self.table.model.df.to_csv(f'{path}')

    # update json file with updated dict
    def update_path_json(self, path_settings):
        # write updated settings dict to file
        with open('path_settings.json', 'w') as f:
            f.seek(0)
            json.dump(path_settings, f, indent=4, sort_keys=True)

    def update_type_json(self, data_types):
        with open('type_dict.json', 'w') as f:
            f.seek(0)
            json.dump(data_types, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    data = DataManager()
    [print(str(var)) for var in vars(data).items()]
