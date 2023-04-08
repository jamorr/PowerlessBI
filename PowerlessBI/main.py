import json
from os import chdir
from os.path import abspath, dirname
from typing import Any, Tuple

import pandas as pd
from customtkinter import CTk, StringVar

from data_manager import DataManager  # noqa: F401
from data_selection_page import SelectData
from import_page import ImportWindow
from plot_page import PlotData
from variable_selection_page import VarWindow

# from scalene import scalene_profiler

""""
do type validation using pydantic or voluptous on save?

SPLIT SAVES INTO THEIR OWN FOLDERS WHICH CONTAIN:
    - json containg:
        - path settings
        - type dict
        - operations performed after import
    - hard reference copy of the file - always tracks where file is moved to
        or if deleted
    - parquet if saved to one
Instead of loading jsons - load folder names first

Create data class outside of main for loading and updating files in storage

USE AWAIT TO PREVENT POP-IN/TO BUFFER??

"""


class WindowManager(CTk):
    """
    Manages various windows and cross window methods for powerless BI

    Args:
        CTk (CTk): Custom Tkinter window
    """
    type_requirements: dict[str, dict[str, Tuple[Any, ...]]] = {
        'Violin': {'X': (1, 'num'), 'y': (1, 'ord'), 'c': (0, 'any')},
        'Ridgeline': {'X': (1, 'num'), 'y': (1, 'ord'), 'c': (0, 'any')},
        'Parallel': {'X': (2, 'any'), 'y': (0, 'any'), 'c': (1, 'any')},
        'Scatter': {'X': (1, 'num'), 'y': (1, 'num'), 'c': (0, 'any')},
        'Histogram': {'X': (1, 'num'), 'y': (0, 'any'), 'c': (0, 'any')},
        'Line': {'X': (1, 'time'), 'y': (1, 'num'), 'c': (1, 'num')},
        'Scatter 3D': {'X': (2, 'num'), 'y': (1, 'num'), 'c': (1, 'any')},
        'Statistics': {'X': (1, 'num', 'ord'), 'y': (0, 'any'), 'c': (0, 'any')},
        'Linear Regression': {'X': (1, 'num'), 'y': (1, 'num'), 'c': (0, 'any')}
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("PowerlessBI")
        self.iconbitmap(r'../assets/POWERLESS_BI_ICON.ico')
        # self.tk.call('tk', 'scaling', 1.5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.data_manager = DataManager()
        self.path_settings: dict
        self.selected_data = StringVar()

        self.selection_window_exists = False

        self.import_window: ImportWindow
        self.import_window_exists = False

        self.sel_window_grid()

    def sel_window_grid(self):
        """Reconfigure window grid\n
        Load existing from JSON\n
        Create selection window if it doesn't exist\n
        Place selection window frames in grid\n
        """
        self.grid_columnconfigure(1, weight=0)
        self.wm_geometry("")
        self.load_json()

        if not self.selection_window_exists:
            # configure comands and init selection_window
            self.selection_window = SelectData(
                self, self.path_settings, self.data_types, self.type_requirements)
            self.selection_window.read_frame.import_button.configure(
                command=self.import_window_grid)
            self.selection_window.read_frame.data_opt.configure(
                variable=self.selected_data)
            for text, button in self.selection_window.ver_frame.vis_buttons.items():
                button.configure(
                    command=(lambda text=text: self.gen_var_window(text)))

            self.selection_window_exists = True
        else:
            self.selection_window.grid()

        # if selected key is not in the current list of keys then reset selected
        if self.selected_data.get() not in list(self.path_settings.keys()):
            self.selected_data.set(value='')
            self.selection_window.read_frame.data_opt.configure(
                values=list(self.path_settings.keys()))

        # fix this
        # self.selection_window.updateButtons()

    def import_window_grid(self):
        """Create import window, remove selection window widgets,
        and set import window widgets on the updated grid
        """
        self.selection_window.grid_remove()
        self.grid_columnconfigure(1, weight=4)

        # create import window or put it into grid and configure buttons
        if not self.import_window_exists:
            self.import_window_exists = True
            self.import_window = ImportWindow(self, self.data_manager)
            self.import_window.file_frame.home_button.configure(
                command=self.import_window_forget_grid)
        else:
            self.import_window.grid()
            self.import_window.view_frame.grid()

    # remove import window widgets
    def import_window_forget_grid(self):
        """remove import_window widgets
        """
        self.import_window.grid_remove()
        self.import_window.view_frame.grid_remove()
        self.sel_window_grid()

    # load json into self.path_settings as dict
    def load_json(self):
        """load json into self.path_settings as dict
        """

        try:
            with open('../path_settings.json', 'r') as f:
                self.path_settings = json.loads(f.read())
        except FileNotFoundError:
            default = {}
            with open('../path_settings.json', 'x') as f:
                f.write(json.dumps(default))
            self.path_settings = default

        try:
            with open('../type_dict.json', 'r') as f:
                self.data_types = json.loads(f.read())
        except FileNotFoundError:
            # File was not found, so create the file and write some default data to it
            default_data = {}
            with open('../type_dict.json', 'x') as f:
                f.write(json.dumps(default_data))
            self.data_types = default_data

    def gen_var_window(self, vis_type):
        """generate window to select options for graph,
        including X and target variables, colors, and seeds.
        """
        self.selection_window.grid_remove()
        self.var_window = VarWindow(
            self, vis_type,
            self.data_types[self.selected_data.get()],
            self.type_requirements[vis_type]
        )
        self.var_window.home_button.configure(command=self.del_var_window)
        self.var_window.right_frame.gen_button.configure(
            command=self.create_vis)

    def del_var_window(self):
        self.var_window.destroy()
        self.sel_window_grid()

    def create_vis(self):
        x_vars = [var for var, tup in self.var_window.x_checkboxes.items()
                  if tup[0].get() is True and var in self.var_window.selectable_x_vars]
        # print(x_vars)
        # check if x_vars are showing
        y_var = self.var_window.selected_y_var.get()
        color = self.var_window.selected_color_var.get()
        color = color if color != '' else None
        vis_type = "_".join(self.var_window.vis_type.lower().split(' ')) + "_plot"
        # instead of data_frame here we could use data manager
        # to load in the data potentially
        data_frame = pd.read_csv(
            **self.path_settings[self.selected_data.get()])
        PlotData(x_vars, y_var, color, vis_type, data_frame, master=self)
        pass


if __name__ == '__main__':
    chdir(dirname(abspath(__file__)))
    # ctypes.windll.shcore.SetProcessDpiAwareness(2)
    root = WindowManager()
    root.mainloop()
