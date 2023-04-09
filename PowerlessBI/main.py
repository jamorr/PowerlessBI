from os import chdir
import os
from os.path import abspath, dirname
from tkinter import messagebox
from typing import Any, Tuple

import pandas as pd
from customtkinter import CTk, StringVar
from padding import Padding

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
        # self.path_settings: dict
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
        # self.load_json()

        if not self.selection_window_exists:
            # configure comands and init selection_window
            self.selection_window = SelectData(
                self,
                # self.path_settings,
                # self.data_types,
                self.data_manager,
                self.type_requirements
            )
            self.selection_window.read_frame.import_button.configure(
                command=self.import_window_grid)
            self.selection_window.read_frame.data_opt.configure(
                variable=self.selected_data)
            # configure button commands for vis creation to
            # call vis with same name as button text
            for text, button in self.selection_window.ver_frame.vis_buttons.items():
                button.configure(command=(lambda text=text: self.gen_var_window(text)))
            self.data_manager.bind(
                "data_selection",
                self.update_save_list_in_data_selection_page
            )
            self.update_save_list_in_data_selection_page()
            # only create sel_window once
            self.selection_window_exists = True
        else:
            self.selection_window.grid()

    def update_save_list_in_data_selection_page(self):
        if self.selected_data.get() not in (saves := self.data_manager.get_saves()):
            self.selected_data.set(value='')
        else:
            self.selection_window.read_dtypes(self.selected_data.get())

        self.selection_window.read_frame.data_opt.configure(values=saves)

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
            self.import_window.grid(
                row=0, column=0,
                sticky='nsew',
                padx=(0, 16)
            )
            # resizes window
            self.wm_geometry("")

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

    def gen_var_window(self, vis_type):
        """generate window to select options for graph,
        including X and target variables, colors, and seeds.
        """
        self.selection_window.grid_remove()
        self.var_window = VarWindow(
            self,
            vis_type,
            self.data_manager.load_selected_dtypes(self.selected_data.get()),
            self.type_requirements[vis_type]
        )
        self.var_window.home_button.configure(command=self.del_var_window)
        self.var_window.right_frame.gen_button.configure(
            command=self.create_vis)
        self.var_window.grid(
            row=0, column=0,
            padx=Padding.LARGE,
            pady=Padding.LARGE,
            sticky="nsew"
        )

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
        settings = self.data_manager.load_selected_settings(self.selected_data.get())

        # match file type to dataframe
        # TODO: #4 add addtional support for other parameters
        parameter_names = [
            "filepath_or_buffer",
            "io",
            "path",
            "query",
            "path_or_buf"
        ]
        for par_name in parameter_names:
            if par_name in settings:
                file_type = os.path.basename(settings[par_name]).split('.')[1]
                break
        else:
            messagebox.showerror("ERROR", "Invalid or missing filepath or buffer.")
            return

        read_method = getattr(pd, "read_"+file_type)
        data_frame = read_method(**settings)
        PlotData(x_vars, y_var, color, vis_type, data_frame, master=self)


if __name__ == '__main__':
    chdir(dirname(abspath(__file__)))
    # ctypes.windll.shcore.SetProcessDpiAwareness(2)
    root = WindowManager()
    root.mainloop()
