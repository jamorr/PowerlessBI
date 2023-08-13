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
import pathlib
import json
import os
import shutil
from typing import Callable, Literal

import pandas as pd
import pandas.io.parsers.c_parser_wrapper as pandas_type_parser
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DirectoryHandler(FileSystemEventHandler):

    def __init__(self, dir_path:pathlib.Path, on_subdirs_update:Callable|None=None):
        # super().__init__()
        super(FileSystemEventHandler, self).__init__()
        self.dir_path:pathlib.Path = dir_path
        self.subdirs:list[str]
        self.on_subdirs_update: Callable|None = None
        self.update_subdirs()
        self.on_subdirs_update = on_subdirs_update

        self.observer = Observer()
        self.observer.schedule(self, self.dir_path, recursive=True)
        self.observer.start()

    def update_subdirs(self):
        self.subdirs = os.listdir(self.dir_path)

    def on_any_event(self, event):
        self.update_subdirs()
        if self.on_subdirs_update:
            self.on_subdirs_update()

    def stop(self):
        self.observer.stop()
        self.observer.join()

# TODO: #9 swap over to use of Path objects with pathlib from os.path strings
class DataManager:
    def __init__(self) -> None:
        self.directory = os.getcwd()
        try:
            self.settings = self.settings_json()
        except FileNotFoundError:
            # TODO: #10 implement run_setup()
            pass
        self.save_path:pathlib.Path = pathlib.Path(self.settings['saves_path'])

        if  not os.path.exists(self.save_path):
            os.mkdir(self.save_path)
        self.dir_handler = DirectoryHandler(
            self.save_path,
            on_subdirs_update=self.update_subdirs
        )
        # below == os.listdir(self.save_path)
        self.save_folders:list[str] = self.dir_handler.subdirs
        self.bound_functions:dict[str, Callable] = {}

    def bind(self, key:str, function:Callable):
        self.bound_functions[key] = function

    def unbind(self, key:str):
        del self.bound_functions[key]

    def update_subdirs(self):
        self.update_save_folders()
        for func in self.bound_functions.values():
            func()

    def settings_json(self):
        """loads PowerlessBI settings found in main folder"""
        with open("../settings.json", "r") as f:
            return json.load(f)

    def update_save_folders(self):
        self.save_folders = self.dir_handler.subdirs

    def get_saves(self) -> list[str]:
        """load existing saves from directory listed in main settings"""
        return self.save_folders

    def delete_selected(self, selected):
        """delete selected save completely"""
        if os.path.exists(self.save_path/selected):
            shutil.rmtree(self.save_path/selected)
        # TODO: add error handling/popup/logging
        # self.save_folders = self.get_saves()

    def rename_selected(self, selected, new_name):
        """rename selected save"""
        # if new names also in path
        try:
            os.rename(self.save_path/selected, self.save_path/new_name)
        except os.error:
            os.mkdir(self.save_path/new_name)

    def load_selected_settings(self, selected:str) -> dict:
        """loads read settings for a save if they exist"""

        try:
            with open(self.save_path/selected/'path_settings.json', 'r') as f:
                path_settings = json.loads(f.read())
        except FileNotFoundError:
            path_settings = {}
        return path_settings

    def load_selected_dtypes(self, selected:str) -> dict:
        """loads dtype settings for save if they exist.
        If they don't and path settings exists, convert dtypes to
        correct format and save."""
        try:
            with open(self.save_path/selected/'type_dict.json', 'r') as f:
                data_types = json.loads(f.read())
        except FileNotFoundError:
            # TODO: make convert dtypes a utility function and call it on
            # path settings if they exist
            # File was not found, so create the file and write some default data to it
            data_types = {}
            # with open(self.save_path+selected+'/type_dict.json', 'x') as f:
            #     f.write(json.dumps(default_data))
            # data_types = default_data

        return  data_types

    def parse_inputs(
        self,
        file_loc:str,
        delim:str|None,
        header:list[int]|Literal['infer'],
        col_names:list[str]|None,
        index_list:list[int]|None,
        data_type:dict[str,str]|None,
        dt_parser_str:list[str]|bool|None,
    ):
        # TODO: implement DT parser
        dt_parser = self.convert_dates(dt_parser_str)
        if dt_parser is None:
            dt_parser = False

        if data_type:
            for dtype in data_type.values():
                try:
                    pandas_type_parser.ensure_dtype_objs(dtype)
                except TypeError:
                    raise TypeError(f"{dtype} is not valid dtype")

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
        """Boolean. If True -> try parsing the index. \n\n
        List of int or names. e.g. If [1, 2, 3] -> try parsing
         columns 1, 2, 3 each as a separate date column. \n\n
        List of lists. e.g. If [[1, 3]] -> combine columns 1
         and 3 and parse as a single date column.
        Dictionary/Hashmap, e.g. {"foo" : [1, 3]} -> parse columns
         1, 3 as date and call result 'foo'"""
        return

    def new_save(self,
                 alias: str,
                 path_settings: dict[str, None | dict | int | list | str],
                 data_types: dict[str, list[str]],
                 operations: list):

        # check if dir exists
        if os.path.exists(self.save_path/alias):
            print("Save already exists.")
            return
        os.mkdir(self.save_path/alias)
        os.mkdir(self.save_path/alias/"data")
        os.mkdir(self.save_path/alias/"plots")

        # create json containing path settings, type dict,
        # and operations performed after import
        # save_settings = {
        #     "path_settings": path_settings,
        #     "data_types": data_types,
        #     "operations": operations
        # }

        with open(self.save_path/alias/'path_settings.json', 'x') as f:
            # f.seek(0)
            json.dump(path_settings, f, indent=4, sort_keys=True)

        with open(self.save_path/alias/'type_dict.json', 'x') as f:
            # f.seek(0)
            json.dump(data_types, f, indent=4, sort_keys=True)


        if (os.path.exists(path_settings['filepath_or_buffer']) and # type:ignore
            path_settings['filepath_or_buffer'] not in
                os.listdir(self.save_path/alias/"data")):
            # create hard reference copy of file
            os.link(path_settings['filepath_or_buffer'], # type: ignore
                    self.save_path/alias/'data'+
                    os.path.basename(path_settings['filepath_or_buffer'])) # type:ignore


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

        settings = self.load_selected_settings(alias)

        # load data from parquet if available
        if os.path.exists(self.save_path/alias/"data/data.parquet"):
            data = pd.read_parquet(self.save_path/alias/"data/data.parquet")
        else:
            data = pd.read_csv(settings["path"]) if settings["type"] == "csv"\
                else pd.read_excel(settings["path"])

        # apply operations as specified in settings
        for operation in settings["operations"]:
            if operation == "dropna":
                data.dropna(inplace=True)
            # add more operations as needed

        return data

    # update json file with updated dict
    def update_path_json(self, selected, path_settings):
        # write updated settings dict to file
        with open(self.save_path/selected/'path_settings.json', 'w') as f:
            f.seek(0)
            json.dump(path_settings, f, indent=4, sort_keys=True)

    def update_type_json(self, selected, data_types):
        with open(self.save_path/selected/'type_dict.json', 'w') as f:
            f.seek(0)
            json.dump(data_types, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    def test_bind():
        print("Bound function called")
    data = DataManager()
    data.bind("test", test_bind)
    [print(str(var)) for var in vars(data).items()]
    params = ("Folds", {
        "converters": None,
        "dtype": {
            "AP": "float64",
            "AT": "float64",
            "PE": "float64",
            "RH": "float64",
            "V": "float64"
        },
        "filepath_or_buffer":
            "C:/Users/Morri/Documents/Notebooks/DSCI1302/Folds test.csv",
        "header": 0,
        "index_col": 0,
        "names": None,
        "parse_dates": False,
        "sep": ","
    },
                  {
        "cat": [],
        "num": [
            "AT",
            "V",
            "AP",
            "RH",
            "PE"
        ],
        "ord": [],
        "time": []
    }, [])
    data.new_save(*params)
    data.delete_selected("Folds")
