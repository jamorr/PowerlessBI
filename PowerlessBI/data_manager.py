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
from types import FunctionType
import pandas as pd
from tkinter import messagebox
import ast
import pandas.io.parsers.c_parser_wrapper as pandas_type_parser

class DataManager:
    def __init__(self) -> None:
        self.directory = os.getcwd()
        self.settings = self.settings_json()
        self.save_path = self.settings['saves_path']
        if os.path.exists(self.save_path):
            self.save_folders = os.listdir(self.save_path)
        else:
            # print("settings path does not exist would you like to set one now?")
            os.mkdir(self.save_path)
            self.save_folders = os.listdir(self.save_path)

    def settings_json(self):
        with open("settings.json", "r") as f:
            return json.load(f)

    def parse_inputs(
        self,
        file_loc:str,
        delim:str,
        rad_var:str,
        col_names:str,
        index_str:str,
        converter_str:str,
        data_type_str:str,
        dt_parser_str:str,
    ):
        # get column names
        if rad_var != 0:
            names = col_names.split(',')
            if rad_var == 1:
                header = 'infer'
            else:
                header = 0
        else:
            names = None
            header = 0

        if index_str != '\n':
            try:
                index = ast.literal_eval(index_str)
            except:
                messagebox.showerror(
                    'ERROR', message='Enter a valid index or list of indices.')
                return None
            if isinstance(index, list):
                for elem in index:
                    if not isinstance(elem, (int, str)):
                        messagebox.showerror('ERROR',
                                             message=f'{elem} is not a valid index.')
                        return None
            elif not isinstance(index, (int, str)):
                messagebox.showerror('ERROR', message='Enter a valid index.')
                return None
        else:
            index = None

        # get converter - read as json
        if converter_str != '\n':
            # check if valid object
            try:
                converter = json.loads(converter_str)
            except:
                messagebox.showerror(
                    'ERROR', message='Enter converter with valid syntax.\n'
                    'See the tool tip (?) for formatting tips.')
                return None

            # check keys and values of dict for correct values
            for key, value in converter.items():

                if not isinstance(key, (int, str)):
                    messagebox.showerror(
                        'ERROR', message=f'Converter key "{key}" is invalid.\n See the'
                        ' tool tip (?) for formatting tips.')
                    return None

                value = eval(value)
                if not isinstance(value, (FunctionType, type)):
                    messagebox.showerror(
                        'ERROR', message=f'Converter value "{value}" is invalid.\n'
                        ' See the tool tip (?) for formatting tips.')
                    return None
        else:
            converter = None

        # get data types for columns
        if data_type_str != '\n':
            data_type = ast.literal_eval(data_type_str)
            if isinstance(data_type, dict):
                try:
                    data_type = {
                        name: str(dtype) for name, dtype in
                        pandas_type_parser.ensure_dtype_objs(data_type).items()
                    }
                except:
                    messagebox.showerror(
                        'ERROR', message='Enter a valid data type dictionary.'
                        ' See the tool tip (?) for formatting tips.')
                    return None
            else:
                messagebox.showerror(
                    'ERROR', message='Enter a valid data type dictionary.'
                    ' See the tool tip (?) for formatting tips.')
                return None
        else:
            data_type = None
        # C:\ProgramData\Anaconda3\envs\DSCI1302\Lib\site-packages\pandas\core\dtypes\common.py
        # pandas>io>parsers>c_parser_wrapper.py>ensure_dtype_objs

        # get date time parser - read as json
        if dt_parser_str != '\n':
            try:
                dt_parser = ast.literal_eval(dt_parser_str)
            except:
                messagebox.showerror(
                    'ERROR', message='Enter a valid date/time parser. See the tool tip'
                    '(?) for formatting tips.')
                return None

        else:
            dt_parser = False

        return {name: set for name, set in zip(['filepath_or_buffer', 'dtype', 'names',
                                                    'header', 'sep', 'index_col',
                                                    'converters', 'parse_dates'],
                                                [file_loc, data_type, names, header,
                                                    delim, index, converter, dt_parser])
                }




    def new_save(self,
                 alias: str,
                 path_settings: dict[str, None | dict | int | list],
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

    def save_data_frame(self):
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
        except:
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
            'filepath_or_buffer': path, 'names': None,
            'header': self.last_import['header']
            if self.last_import is not None else 'infer',
            'sep': ",", 'index_col': index_name if index_name is not None else 0,
            'converters': None, 'parse_dates': False
        }

        # save file to path and save path to json
        self.table.model.df.to_csv(f'{path}')

    # update json file with updated dict
    def update_path_json(self):
        # write updated settings dict to file
        with open('path_settings.json', 'w') as f:
            f.seek(0)
            json.dump(self.path_settings, f, indent=4, sort_keys=True)

    def update_type_json(self):
        with open('type_dict.json', 'w') as f:
            f.seek(0)
            json.dump(self.data_types, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    data = DataManager()
    [print(str(var)) for var in vars(data).items()]
