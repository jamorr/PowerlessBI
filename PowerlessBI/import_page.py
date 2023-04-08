import ast
from types import FunctionType
import json
import os
import tkinter.messagebox as messagebox
from datetime import datetime
from tkinter.filedialog import askopenfilename
import tkinter as tk
from typing import Any
from warnings import catch_warnings, simplefilter  # noqa: F401
from collections import Counter, deque


from padding import Padding
from customtkinter import (END, CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkOptionMenu, CTkRadioButton, CTkTextbox, E, W,
                           IntVar, StringVar, ScalingTracker, CTkInputDialog,
                           CTkScrollableFrame, CTkSwitch, BooleanVar)
from pandastable import Table
from ctk_tooltip import CTkTooltip
# import numpy as np
# import pandas as pd
from pandas import read_csv
from pandas.io.parsers.c_parser_wrapper import ensure_dtype_objs
from data_manager import DataManager  # noqa: F401
from utils import UpDownButtons
from numpy import sctypeDict

"""
use a json file but store the converter as a string
on import eval() the converter
use voluptuous for type coercion/validation for inputs?

save file -> save to parquet or arrow or shelf/pickle
read only first 100 or so lines initially to evaluate the file
- add button that gets header settings
- add button that optimizes dtypes
- add button that transposes data frame
- add button that scales data

if screen is not wid enough add horizontal scroll bar or move the spread
sheet to the bottom
"""
TYPES = (
    "",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float32",
    "float64",
    "datetime",
    "timedelta",
)


class FileFrame(CTkFrame):
    """
    Frame to select data source. Can clear the form and choose data from existing.

    Args:
        CTkFrame (_type_): _description_
    """

    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        self.grid_columnconfigure(2, weight=0)

        self.home_button = CTkButton(self, width=28, text='⌂',
                                     text_color='black', fg_color='#517f47',
                                     hover_color='#385831')
        self.home_button.grid(row=0, column=0, padx=Padding.LEFT,
                              pady=Padding.TOP, sticky="ns", stick=W)

        CTkLabel(self, text='Select file to read in:',
                 anchor='center').grid(row=0, padx=Padding.RIGHT,
                                       pady=Padding.TOP, sticky="ns",
                                       columnspan=2)

        self.clear_button = CTkButton(self, text='Clear Form',
                                      fg_color='#8b0000',
                                      hover_color='#650000')
        self.clear_button.grid(row=0, column=2, stick=W,
                               padx=Padding.RIGHT, pady=Padding.TOP)

        self.path_entry = CTkEntry(self, width=300)
        self.path_entry.grid(row=1, column=0, padx=Padding.LEFT,
                             pady=Padding.SMALL, sticky="nsew",
                             columnspan=2)

        self.browse_button = CTkButton(self, text="Browse")
        self.browse_button.grid(row=1, column=2, padx=Padding.RIGHT,
                                pady=Padding.SMALL, stick=W)

        CTkLabel(self, text='Edit existing:',
                 anchor='center').grid(row=2, column=0, padx=Padding.LEFT,
                                       pady=Padding.BOTTOM, sticky="ns", stick=E)

        self.path_settings_option = CTkOptionMenu(self, anchor='center')

        self.path_settings_option.grid(row=2, column=1, padx=Padding.RIGHT,
                                       pady=Padding.BOTTOM, sticky="ns", stick=W)

        self.del_button = CTkButton(self, text="Delete Selected",
                                    fg_color=("gray95", "gray10"),
                                    state='disabled')

        self.del_button.grid(row=2, column=2, padx=Padding.RIGHT,
                             pady=Padding.BOTTOM, stick=W)


class SettingsFrame(CTkFrame):

    def __init__(self, master: CTkFrame):
        CTkFrame.__init__(self, master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)  # type: ignore

        self.rad_var = IntVar(value=0)

        CTkLabel(self, text='Set separator character(s):',
                 anchor='e').grid(row=0, column=0, stick=W,
                                  padx=Padding.LEFT, pady=Padding.TOP)

        self.delim_entry = CTkEntry(self, width=20)
        self.delim_entry.grid(row=0, column=0, stick=E,
                              sticky='nse', padx=Padding.RIGHT,
                              pady=Padding.TOP)

        CTkLabel(self, text='Set column names:',
                 anchor='e').grid(row=1, column=0, stick=W,
                                  padx=Padding.LARGE, pady=Padding.TOP)

        self.header_rad_0 = CTkRadioButton(self, value=0, variable=self.rad_var,
                                           command=self.set_columns,
                                           text="Use row as column names",)

        self.header_rad_0.grid(row=2, column=0, stick=W,
                               padx=Padding.LEFT, pady=Padding.SMALL)

        # add button to replace existing names
        self.header_rad_1 = CTkRadioButton(self, variable=self.rad_var,
                                           value=1, command=self.set_columns,
                                           text="Infer column names")
        self.header_rad_1.grid(row=3, column=0, stick=W,
                               padx=Padding.LEFT, pady=Padding.SMALL)

        # consider using textbox
        # https://github.com/TomSchimansky/CustomTkinter/wiki/CTkTextbox
        self.header_row_number_entry = CTkEntry(
            self,
            placeholder_text="Enter row indices to use as header separated by ','",
            width=250, fg_color=("gray95", "gray10")
        )
        self.header_row_number_entry.grid(row=5, column=0, sticky='nsew',
                                          padx=(40, 16), pady=Padding.BOTTOM)
        self.header_row_number_entry.configure(state='disabled')

    # focus or unfocus from entry box, change color and replace placeholder text

    def set_columns(self):
        if self.rad_var.get() == 0:
            self.focus()
            self.header_row_number_entry.configure(
                fg_color=("gray95", "gray10"))
            self.header_row_number_entry._activate_placeholder()
            self.header_row_number_entry.configure(state='disabled')
        else:
            self.header_row_number_entry.configure(
                state='normal', fg_color=("#F9F9FA", "#343638"))
            self.header_row_number_entry.focus()


class ActionFrame(CTkFrame):
    def __init__(self, master: CTkFrame):
        super().__init__(master)

        self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        self.grid_rowconfigure((0, 1, 2, 3), weight=0)  # type: ignore

        self.import_button = CTkButton(self, text='Import Data',)
        self.import_button.grid(row=0, columnspan=2,
                                padx=Padding.LARGE, pady=Padding.TOP)

        # save data or save path
        self.alias_entry = CTkEntry(self, width=250,
                                    placeholder_text='Enter alias, defaults to file name')
        self.alias_entry.grid(row=1, column=0, columnspan=2,
                              padx=Padding.LARGE, pady=Padding.TOP,)

        self.save_fp_button = CTkButton(self, text='Save frame & path',)
        self.save_fp_button.grid(row=2, column=0, padx=Padding.LEFT,
                                 pady=Padding.SMALL, sticky='ns', stick=E)

        self.save_path_button = CTkButton(self, text='Save path',)
        self.save_path_button.grid(row=2, column=1, padx=Padding.RIGHT,
                                   pady=Padding.SMALL, sticky='ns', stick=W)

        self.save_label = CTkLabel(self, text='')
        self.save_label.grid(row=3, column=0, columnspan=2,
                             padx=Padding.LARGE, pady=Padding.BOTTOM,
                             sticky='ns')


"""
Parse names for each column name
Add dropdowns to select data types for each column name
Add switches to select if a column is an index column
Add drop downs/format textboxes for date time

x <Col name> <dtype> <index> <datetime>
"""


class SettingsRow(CTkFrame):
    def __init__(
        self,
        master,
        name: str | None = None,
        is_index: bool = False,
        data_type: str = '',
        date_time: str = ''
    ):
        super().__init__(master)
        # self.grid_configure(column=5, row = 1)

        self.name = StringVar(value=name)
        self.is_index = BooleanVar(value=is_index)
        self.data_type = StringVar(value=data_type)
        self.date_time = StringVar(value=date_time)

        self.name_entry = CTkEntry(
            self, textvariable=self.name)
        self.name_entry.grid(
            column=0, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.index_switch = CTkSwitch(
            self, width=36, variable=self.is_index, text="")
        self.index_switch.grid(
            column=1, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.data_type = CTkOptionMenu(
            self,
            # values=[str(key) for key in sctypeDict.keys()],
            values=TYPES,  # type: ignore
            variable=self.data_type
        )
        self.data_type.grid(
            column=2, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.date_time_entry = CTkEntry(
            self, textvariable=self.date_time)
        self.date_time_entry.grid(
            column=3, row=0,
            sticky="nsew",
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )

    def del_row(self):
        self.grid_forget()
        del self

# TODO: add to rows buttons to move row up and down
# shift click -> move to top or bottom
# add new row -> scroll down to center the new row


class ColumnSettingsFrame(CTkScrollableFrame):

    def __init__(self, master: CTkFrame):
        CTkScrollableFrame.__init__(
            self,
            master,
            label_text="Column Settings"
        )

        self.rows: list[SettingsRow] = []
        self.del_buttons: list[CTkButton] = []
        self.up_down_buttons: list[UpDownButtons] = []
        self.last_row_index = 2

        self.grid(row=2, rowspan=2, column=1, sticky='nsew',
                  padx=Padding.RIGHT, pady=Padding.BOTTOM)

        CTkButton(
            self, width=28, text="x",
            fg_color='#8b0000',
            hover_color='#650000',
            command=self.del_all_rows
        ).grid(
            row=0, column=0,
            sticky="ew",
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=140,
            text="Column Name"
        ).grid(
            row=0, column=1,
            sticky='nsew',
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=36,
            text="Index"
        ).grid(
            row=0, column=2,
            sticky='nsew',
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=140,
            text="Data Type"
        ).grid(
            row=0, column=3,
            sticky='nsew',
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=140,
            text="Date Time"
        ).grid(
            row=0, column=4,
            sticky='nsew',
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        self.new_row_button = CTkButton(self, text="+", command=self.add_row)
        self.new_row_button.grid(row=1, column=1)

    def add_row(
        self,
        name: str | None = None,
        is_index: bool = False,
        data_type: str = '',
        date_time: str = ''
    ):
        """add a row to grid

        Args:
            name (str|None, optional): Name for new row. Defaults to None.
        """
        self.grid_rowconfigure(self.last_row_index+2)
        self.rows.append(SettingsRow(
            self,  name, is_index, data_type, date_time))
        self.rows[-1].grid(
            column=1, row=self.last_row_index, columnspan=4, sticky='ew',
            pady=4)
        del_button = CTkButton(
            self, width=28, text="x",
            fg_color='#8b0000',
            hover_color='#650000',
        )
        self.del_buttons.append(del_button)
        # print(del_button.grid_info())
        del_button.configure(
            command=(lambda button=del_button: self.del_row(button)))
        del_button.grid(
            column=0, row=self.last_row_index,
            sticky='ew', padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        up_down_button = UpDownButtons(
            self,
            lambda button=del_button: self.move_row_up(button),
            lambda button=del_button: self.move_row_down(button),
            lambda button=del_button: self.move_row_to_top(button),
            lambda button=del_button: self.move_row_to_bottom(button),
            disable_up=(len(self.rows) == 1),
            disable_down=True
        )
        up_down_button.grid(
            column=5,
            row=self.last_row_index,
            sticky='ew', padx=Padding.SMALL,
            pady=Padding.SMALL
        )
        self.up_down_buttons.append(up_down_button)
        # set previous buttons down button to enabled
        if len(self.rows) > 1:
            self.up_down_buttons[-2].activate_down()
        self.last_row_index += 1
        self.new_row_button.grid(row=self.last_row_index)
        self.focus_end()

    def focus_end(self):
        self._parent_canvas.configure(scrollregion=self._parent_canvas.bbox("all"))
        # self._fit_frame_dimensions_to_canvas()
        # TODO: scroll to better center newly added text box
        # Create a dummy event object
        event = tk.Event()

        # Set the attributes of the event object to simulate a scroll event
        event.delta = -120  # Positive value for scrolling up, negative for scrolling down
        event.x = self.winfo_pointerx()
        event.y = self.winfo_pointery()
        event.widget = self._parent_canvas
        self._mouse_wheel_all(event)
        # self._parent_canvas.yview_scroll(120, "units")
        print(f"Before: {self._parent_canvas.yview()}")
        # self._parent_canvas.yview_moveto(1.0)
        # print(f"After: {self._parent_canvas.yview()}")


    def del_all_rows(self):
        while self.del_buttons:
            del_button = self.del_buttons[-1]
            del_button.invoke()

    def swap_rows(self, row1, row2):
        # messagebox.showinfo('', f'swap row {row1-1} with row {row2-1}')
        self.rows[row1-1].grid(row=row2+1)
        self.rows[row2-1].grid(row=row1+1)
        self.rows[row1-1], self.rows[row2-1] = \
            self.rows[row2-1], self.rows[row1-1]

    def move_row_up(self, del_button):
        row = self.del_buttons.index(del_button) + 1
        self.swap_rows(row, row-1)

    def move_row_down(self, del_button):
        row = self.del_buttons.index(del_button) + 1
        self.swap_rows(row, row+1)

    def move_row_to_top(self, del_button):
        row = self.del_buttons.index(del_button) + 1
        while row > 1:
            self.swap_rows(row, row-1)
            row -= 1

    def move_row_to_bottom(self, del_button):
        row = self.del_buttons.index(del_button) + 1
        while row < len(self.rows):
            self.swap_rows(row, row+1)
            row += 1

    def reset(self):
        """Sets all row values to defaults
        """
        for row in self.rows:
            row.name.set('')
            row.name_entry.delete(0, END)
            row.is_index.set(False)
            row.data_type.set('')
            row.date_time.set('')
            row.date_time_entry.delete(0, END)

    def del_row(self, row):
        if type(row) is not int:
            try:
                row = self.del_buttons.index(row)
            except TypeError:
                return

        # print(f"Delete row {row}/{len(self.rows)-1}")
        if 0 > row > len(self.rows) - 1:
            return
        self.up_down_buttons[-1].grid_remove()
        # self.up_down_buttons[-1].destroy()
        del self.up_down_buttons[-1]
        self.del_buttons[-1].grid_remove()
        # self.del_buttons[row].destroy()
        del self.del_buttons[-1]
        self.rows[row].del_row()
        # self.rows[row].destroy()
        del self.rows[row]
        for r in self.rows[row:]:
            new_row = r.grid_info()['row'] - 1
            r.grid_configure(row=new_row)

        if len(self.up_down_buttons) > 0:
            self.up_down_buttons[-1].disable_down()  # type: ignore
            self.up_down_buttons[0].disable_up()

    def get_settings(self):
        """Get all data from rows and return in a dict

        Returns:
            dict: settings from rows
        """
        names = []
        indices = []
        data_types = []
        datetime = []

        for _, row in enumerate(self.rows):
            names.append(row.name.get())
            indices.append(row.is_index.get())
            data_types.append(row.data_type.get())
            datetime.append(row.date_time.get())

        return {"col_names": names,
                "indices": indices,
                "dtypes": data_types,
                "datetime": datetime}

    def set_all(self, settings: dict[str, list]):
        if self.rows:
            if not messagebox.askokcancel(
                "WARNING",
                "Proceeding will clear existing rows. Continue anyways?"
            ):
                return
        self.del_all_rows()


        rows = [
            {
                'name': settings['names'][i] if settings['names'][i] else '',
                'is_index':True if i in settings['index'] else False,
                'data_type':settings['dtype'][settings['names'][i]]
                if settings['names'][i] in settings['dtype'] else '',
                # depends on settings in main settings
                # by default: MM/DD/YYYY
                'date_time':''
            }
            for i in range(len(settings['dtype']))
        ]
        for row in rows:
            self.add_row(**row)


class ViewFrame(CTkFrame):
    def __init__(self, master: CTk, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(
            row=0, column=1,
            sticky="nsew"
        )


class ImportWindow(CTkFrame):
    """
    Create page where data file can be selected, read in, transformed, viewed,
    edited, and deleted \n\n
    Path and import settings can be saved to path_settings.json
    """

    def __init__(self, master: CTk, data_manager: DataManager) -> None:
        """initialize ImportWindow

        Args:
            master (CTk): master window
            path_settings (dict):  dict containing settings for existing data
        """

        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        self.grid_rowconfigure((0, 1, 2, 3), weight=0)  # type: ignore
        self.grid_rowconfigure(4, weight=1)
        self.grid(row=0, column=0,
                  sticky='nsew',
                  padx=(0, 16))

        # self.data_types = data_types
        # self.path_settings = path_settings
        self.data_manager = data_manager
        self.path_settings_alias = ['']
        self.path_settings_alias.extend(
            list(self.data_manager.get_path_settings()))

        self.path_text = StringVar()
        self.delim = StringVar(value='')

        self.selected = StringVar()
        self.last_import = None  # list of import settings from last import

        # create frame to select path and import existing
        self.file_frame = FileFrame(self)
        self.file_frame.browse_button.configure(command=self.browse_func)
        self.file_frame.clear_button.configure(command=self.clear_form)
        self.file_frame.path_entry.configure(textvariable=self.path_text)
        self.file_frame.path_settings_option.configure(variable=self.selected,
                                                       values=self.path_settings_alias,
                                                       command=self.fill_form)
        self.file_frame.del_button.configure(command=self.del_selected)
        self.file_frame.grid(row=0, column=0, columnspan=2,
                             sticky="nsew", padx=Padding.LARGE,
                             pady=Padding.TOP)
        # create frame to input settings
        self.settings_frame = SettingsFrame(self)
        self.settings_frame.delim_entry.configure(textvariable=self.delim)
        self.settings_frame.grid(row=1, column=0, sticky="nsew",
                                 padx=Padding.LEFT, pady=Padding.SMALL)

        # create frame for action buttons
        self.act_frame = ActionFrame(self)
        self.act_frame.import_button.configure(command=self.import_data)
        self.act_frame.save_fp_button.configure(command=self.save_data_frame)
        self.act_frame.save_path_button.configure(command=self.save_prep)
        self.act_frame.grid(row=1, column=1, sticky="new",
                            padx=Padding.RIGHT, pady=Padding.SMALL)
        # create frame for advanced options
        self.adv_frame = ColumnSettingsFrame(self)
        self.adv_frame.grid(row=2, rowspan=3, column=0, columnspan=2, sticky="nsew",
                            padx=Padding.LARGE, pady=Padding.BOTTOM)

        screen_width = self.winfo_screenwidth()
        height = self.winfo_height()
        master.geometry(f'{screen_width}x{height}')

        # create frame and table to display data
        self.view_frame = ViewFrame(
            master, width=screen_width-self.winfo_width())

        # get dpi scaling from master
        # dpi_scale = master.winfo_screenheight() / master.winfo_screenmmheight()
        dpi_scale = ScalingTracker.get_window_dpi_scaling(master)

        # Use the scaling factor to set the font size and row height of the pandastable
        font_size = int(14 * dpi_scale)  # type:ignore
        row_height = int(20 * dpi_scale)  # type:ignore

        # assign font size and row height with kwargs and construct table
        self.table = Table(parent=self.view_frame,
                           # showstatusbar=True,showtoolbar=True,
                           **{'thefont': ('Arial', font_size),
                              'rowheight': row_height})
        self.table.show()
        # self.table.setTheme('bold')

    # show frames
    # remove this?

    def grid_set(self):
        if self.last_import is not None:
            # self.grid_columnconfigure(1, weight=2)  # type: ignore
            self.view_frame.grid()

    # update json file with updated dict
    def update_path_json(self):
        # write updated settings dict to file
        with open('path_settings.json', 'w') as f:
            f.seek(0)
            json.dump(self.path_settings, f, indent=4, sort_keys=True)
        self.path_settings_alias = ['']
        self.path_settings_alias.extend(self.path_settings)
        self.file_frame.path_settings_option.configure(
            values=self.path_settings_alias)

    def update_type_json(self):
        with open('type_dict.json', 'w') as f:
            f.seek(0)
            json.dump(self.data_types, f, indent=4, sort_keys=True)

    # delete selected from dict
    def del_selected(self):
        selected = self.selected.get()
        self.log_action('Deleted path', selected)
        # del self.path_settings[selected]
        self.data_manager.delete_selected(selected)
        # change to blue
        self.file_frame.del_button.configure(
            fg_color=["gray95", "gray10"], state='disabled')
        self.selected.set('')

        self.data_manager.update_path_json(self.path_settings)

    # find file and set entry box to path
    def browse_func(self):
        filename = askopenfilename(filetypes=(
            ("CSV files", "*.csv"), ("All files", "*.*")))
        self.path_text.set(filename)

    # TODO: Implement parser for DateTime
    def parse_dt(self, dt):
        """Boolean. If True -> try parsing the index. \n\n
        List of int or names. e.g. If [1, 2, 3] -> try parsing
         columns 1, 2, 3 each as a separate date column. \n\n
        List of lists. e.g. If [[1, 3]] -> combine columns 1
         and 3 and parse as a single date column.
        Dictionary/Hashmap, e.g. {"foo" : [1, 3]} -> parse columns
         1, 3 as date and call result 'foo'"""
        return False
    ### add type checking ###
    # read settings and do type checkikng

    def read_form(self):
        # get path
        file_loc = self.path_text.get()  # check validity later
        rad_var = self.settings_frame.rad_var.get()  # always valid
        delim = self.delim.get() if self.delim.get() else None
        adv_settings = self.adv_frame.get_settings()
        if adv_settings:
            index: list[int] | None = [i for i, b_var in enumerate(adv_settings["indices"])
                                       if b_var]
            names: list[str] | None = adv_settings['col_names']
            # validate names
            names_counts = Counter(names)
            if (len(names) < len(names_counts) and
                    messagebox.askyesno(
                    "Name overlap:",
                    "Append duplicate names with numbers?")
                    ):
                # create list of unique/mangled names
                t_names = deque(maxlen=len(names))
                for name in names[::-1]:
                    t_names.appendleft(name+f"{names_counts[name]}")
                    names_counts[name] -= 1
                names = list(t_names)

            data_type: dict[str, str] | None = {name: dtype
                                                for name, dtype in zip(names, adv_settings['dtypes']) if dtype}
            dt_parser: bool | list[int] | list[str] = self.parse_dt(
                adv_settings['datetime'])
        else:
            names = None
            # header = 'infer'
            index = None
            data_type = None
            dt_parser = False

        # self.data_manager.process()
        # get column names

        settings = self.data_manager.parse_inputs(
            file_loc,
            delim,
            rad_var,
            names,
            index,
            data_type,
            dt_parser
        )
        if settings is None:
            raise TypeError
        return settings

        # C:\ProgramData\Anaconda3\envs\DSCI1302\Lib\site-packages\pandas\core\dtypes\common.py
        # pandas>io>parsers>c_parser_wrapper.py>ensure_dtype_objs

    def clear_form(self):
        self.path_text.set('')
        self.delim.set('')
        if self.selected.get() != '':
            self.selected.set('')
            self.file_frame.del_button.configure(fg_color=["gray95", "gray10"],
                                                 state='disabled')

        # delete entry then activate placeholder and change rad button
        # self.settings_frame.col_name_entry._entry.delete(0, END)
        # self.settings_frame.col_name_entry._activate_placeholder()
        self.settings_frame.rad_var.set(0)

        # delete alias entry and activate placeholder
        self.act_frame.alias_entry._entry.delete(0, END)
        self.act_frame.alias_entry._activate_placeholder()

        # delete adv frame entry
        self.adv_frame.reset()

        self.focus()

    # fill in form with the selected file's settings
    def fill_form(self, selected):
        if selected == '':
            self.file_frame.del_button.configure(
                fg_color=["gray95", "gray10"], state='disabled')
            return None

        # change delete button to red
        self.file_frame.del_button.configure(
            fg_color='#8b0000', hover_color='#650000', state='normal')

        # fill path box
        settings = self.data_manager.load_selected_settings(selected) # path_settings[selected]
        # settings = self.data_manager.read_settings(selected)
        self.path_text.set(settings['filepath_or_buffer'])

        # fill delim box
        delim = settings['sep'] if ('sep' in settings) and (settings['sep'] is not None) else ''
        if delim is None:
            delim = ''
        self.delim.set(delim)

        # select radio button and fill header names
        # if settings['names'] is not None:
        #     if settings['header'] == 0:
        #         self.settings_frame.rad_var.set(1)
        #     else:
        #         self.settings_frame.rad_var.set(2)
        #     self.settings_frame.set_columns()
        #     self.fill_placeholder_entry(self.settings_frame.col_name_entry,
        #                                 settings['names'])
        # else:
        #     self.settings_frame.rad_var.set(0)

        # fill alias entry box
        self.fill_placeholder_entry(self.act_frame.alias_entry, selected)
        # fill rows in adv_frame
        adv_frame_settings = {
            'names': settings['names'],
            'is_index': settings['index_col'],
            'dtype': settings['dtype'],
            # TODO: implement date conversion based on default from settings

            'parse_dates': self.data_manager.convert_dates(settings['parse_dates'])
        }
        self.adv_frame.set_all(adv_frame_settings)
        # fill converter box

        self.focus()

        # import based on settings
        if self.last_import is not None:
            if self.last_import == settings:
                return
            else:
                self.table.clearTable()
        else:
            self.grid_set()

        self.last_import = settings

        self.add_df(settings)

    def fill_placeholder_entry(self, entry: CTkEntry, text):
        entry._deactivate_placeholder()
        entry._entry.delete(0, END)
        entry._entry.insert(0, str(text).replace("'", '"'))
        entry._activate_placeholder()

    def fill_textbox(self, textbox: CTkTextbox, text:str|None):

        if text is None:
            text = ''
        text = str(text).replace("'", '"')
        text = ',\n'.join(text.split(','))
        textbox.delete('0.0', 'end')
        textbox.insert('0.0', text)

    # import data with settings and display in frame
    def import_data(self):
        # read settings from form

        settings = self.read_form()
        if settings is None:
            messagebox.showerror("Error", "Invalid import settings.")
            return None

        # clear table if there is data on it
        if self.last_import is not None:
            self.last_import = settings
            self.table.clearTable()
        else:
            self.last_import = settings
            self.grid_set()

        self.add_df(settings)

    def convert(self, converter):
        temp = {}
        for key, value in converter.items():
            try:
                temp[key] = eval(value)
            except:
                temp[key] = value
        return temp

    def add_df(self, settings_in: dict):
        settings = settings_in.copy()

        if isinstance(settings['dtype'], dict):
            settings['dtype'] = self.convert(settings['dtype'])

        # try:
        self.table.model.df = read_csv(**settings)
        # except Exception as e:
        #     # Display a custom error message along with the exception
        #     messagebox.showerror("Error", "An error occurred:\n\n" + str(e))
        #     return

        # show index if present and format table
        self.table.showindex = True
        self.table.autoResizeColumns()
        self.table.show()

    # save the settings to path_settings.json
    # delete old settings if alias changed but selection is the same
    # update the options bar to reflect new
    def save_prep(self):
        # change the names back?
        form = self.read_form()
        if form is None:
            messagebox.showerror("Error", "Invalid import settings.")
            return
        self.save_path(form)

    def save_path(self, form):
        if os.path.basename(self.path_text.get()) == '':
            messagebox.showerror('ERROR', message='Select a file')
            return 0
        # get alias or file name if no alias
        alias = self.act_frame.alias_entry.get() if self.act_frame.alias_entry.get() \
            else os.path.basename(self.path_text.get()).split('.')[0]
        if self.last_import != form:
            self.add_df(form)
            # if add_df returns none then return none

        settings = form
        if settings['dtype'] is None:
            dtypes = [str(dtype) for dtype in self.table.model.df.dtypes]
            columns = [name for name in self.table.model.df.columns]
            names_types = {name: dtype for name, dtype in zip(columns, dtypes)}
            settings['dtype'] = names_types
        # test
        # print([str(dtype) for dtype in self.table.model.df.dtypes])
        selected = self.selected.get()
        if selected != '':
            if alias != selected:
                self.data_manager.rename_selected(selected, alias)
                # del self.path_settings[selected]

        # update dict with new settings
        # self.path_settings.update(settings)

        converted_types = self.read_dtypes(settings['dtype'])

        if alias in self.data_manager.get_path_settings():
            # update path settings json
            self.data_manager.update_type_json(alias, converted_types)
            self.data_manager.update_path_json(alias, settings)
        else:
            self.data_manager.new_save(alias, settings, converted_types, [])
        # fill form
        self.selected.set(alias)
        self.fill_form(alias)
        self.log_action('Saved path', alias)

    # add popup that gets file path to save file to and file name
    # change so that it doesnt save default index column
    # select file location to save to
    # saves a copy of the data to the selected file location
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
                'Warning', message='Overwrite the selected path?\n'
                'Select Yes to proceed, No to save without overwriting,'
                ' or Cancel to exit.')

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
        self.log_action('Saved data', alias)

        # save settings
        save_try = self.save_path(settings)
        if save_try == 0:
            messagebox.showerror("ERROR", message="Failed to save path.")
            return None
        self.log_action('Saved data and path', alias)

    def check_alias(self, alias: str | None):
        """Check if alias has been entered and warn if overwriting existing"""
        if alias == '':
            warn_bool = messagebox.askyesnocancel(
                title="Warning",
                message='Saving without an alias will use the name of \n'
                'original file as an alias, and overwrite it.\n '
                'Select Yes to proceed, No to enter an alias, or Cancel to exit.'
            )
        else:
            return alias

        if warn_bool is True:
            return os.path.basename(self.path_text.get()).split('.')[0]
        elif warn_bool is False:
            alias_pop = CTkInputDialog(
                text="Type in an alias:", title="Alias Entry")
            return self.check_alias(alias=alias_pop.get_input())
        else:
            return None

    # rework to remove y var and read in existing saves?
    # save list of dtypes to separate json/shelf
    def read_dtypes(self, dtype: dict):
        dtypes_dict = self.reverse_dict(dtype)
        print(dtypes_dict)
        # convert dtypes into appropriate forms
        types_dict = {
            'num': [],
            'ord': [],
            'cat': [],
            'time': [],
        }

        for key, value in dtypes_dict.items():
            types_dict = self.convert_dtype(key[:3], value, types_dict)

        return types_dict

    def convert_dtype(self, key_3: str, value, types_dict):
        if key_3.upper() == 'UIN':  # np.uint..
            types_dict['ord'] += value
        elif key_3.upper() in ['FLO', 'INT']:  # np.float.. np.int..
            types_dict['num'] += value
        elif key_3.upper() in ['DAT', 'TIM', 'PER']:  # np.datetime64, pd.TimeDelta
            types_dict['time'] += value
        else:
            types_dict['cat'] += value

        # types_dict['any'] += value

        return types_dict

    def reverse_dict(self, d: dict):
        output = {}
        for k, v in d.items():
            if v in output:
                output[v].append(k)
            else:
                output[v] = [k]
        return output

    # update log label to show last action

    def log_action(self, action: str, alias: str):
        now = datetime.now()
        dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
        save_text = f'{dt_string} -- {action} of "{alias}"'
        self.act_frame.save_label.configure(text=save_text)


if __name__ == '__main__':
    from os import chdir
    from os.path import abspath, dirname
    app = CTk()
    chdir(dirname(abspath(__file__)))
    app.grid_columnconfigure((0, 1), weight=1)  # type: ignore
    import_win = ImportWindow(app, DataManager())
    app.mainloop()
