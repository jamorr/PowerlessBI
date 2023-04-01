import ast
from types import FunctionType
import json
import os
import tkinter.messagebox as messagebox
from datetime import datetime
from tkinter.filedialog import askopenfilename
from warnings import catch_warnings, simplefilter

from padding import Padding
from customtkinter import (END, CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkOptionMenu, CTkRadioButton, CTkTextbox, E, W,
                           IntVar, StringVar, ScalingTracker, CTkInputDialog,
                           CTkTabview, CTkScrollableFrame)
from pandastable import Table
from ctk_tooltip import CTkTooltip
import numpy as np
import pandas as pd
from pandas import read_csv
from pandas.io.parsers.c_parser_wrapper import ensure_dtype_objs
from utils import ScrolledFrame
from data_manager import DataManager
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

if screen is not wid enough add horizontal scroll bar or move the spread sheet to the bottom
"""


class FileFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        self.grid_columnconfigure(2, weight=0)

        self.grid(row=0, column=0, columnspan=2,
                  sticky="nsew", padx=Padding.LARGE,
                  pady=Padding.TOP)

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
                                    # type: ignore
                                    fg_color=["gray95", "gray10"],
                                    state='disabled')

        self.del_button.grid(row=2, column=2, padx=Padding.RIGHT,
                             pady=Padding.BOTTOM, stick=W)


class SettingsFrame(CTkFrame):

    def __init__(self, master: CTkFrame):
        CTkFrame.__init__(self, master)

        self.grid(row=1, rowspan=2, column=0, sticky="nsew",
                  padx=Padding.LEFT, pady=Padding.SMALL)

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
                                           text="Use first row as column names",)

        self.header_rad_0.grid(row=2, column=0, stick=W,
                               padx=Padding.LEFT, pady=Padding.SMALL)

        # add button to replace existing names
        self.header_rad_1 = CTkRadioButton(self, variable=self.rad_var,
                                           value=1, command=self.set_columns,
                                           text="Create column names")
        self.header_rad_1.grid(row=3, column=0, stick=W,
                               padx=Padding.LEFT, pady=Padding.SMALL)

        self.header_rad_2 = CTkRadioButton(self, variable=self.rad_var,
                                           value=2, command=self.set_columns,
                                           text="Replace column names",)
        self.header_rad_2.grid(row=4, column=0, stick=W,
                               padx=Padding.LEFT, pady=Padding.SMALL)

        # consider using textbox
        # https://github.com/TomSchimansky/CustomTkinter/wiki/CTkTextbox
        self.col_name_entry = CTkEntry(self,
                                       placeholder_text=
                                       "Enter column names separated by ','",
                                       width=250, fg_color=["gray95", "gray10"])
        self.col_name_entry.grid(row=5, column=0, sticky='nsew',
                                 padx=(40, 16), pady=Padding.BOTTOM)
        self.col_name_entry.configure(state='disabled')


    # focus or unfocus from entry box, change color and replace placeholder text
    def set_columns(self):
        if self.rad_var.get() == 0:
            self.focus()
            self.col_name_entry.configure(fg_color=["gray95", "gray10"])
            self.col_name_entry._activate_placeholder()
            self.col_name_entry.configure(state='disabled')
        else:
            self.col_name_entry.configure(
                state='normal', fg_color=["#F9F9FA", "#343638"])
            self.col_name_entry.focus()


class ActionFrame(CTkFrame):
    def __init__(self, master: CTkFrame):
        super().__init__(master)
        self.grid(row=1, column=1, sticky="new",
                  padx=Padding.RIGHT, pady=Padding.SMALL)
        self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        self.grid_rowconfigure((0, 1, 2, 3), weight=0)  # type: ignore

        self.import_button = CTkButton(self, text='Import Data',)
        self.import_button.grid(row=0, columnspan=2,
                                padx=Padding.LARGE, pady=Padding.TOP)

        # save data or save path
        self.alias_entry = CTkEntry(self, width=250,
                                    placeholder_text=
                                    'Enter alias, defaults to file name')
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


class AdvancedSettingsFrame(CTkTabview):
    def __init__(self, master: CTkFrame):
        super().__init__(master)
        # self.grid_rowconfigure(0, weight=1)
        # self.grid_columnconfigure((0, 1), weight=1)  # type: ignore

        self.grid(row=2, rowspan=2, column=1, sticky='nsew',
                  padx=Padding.RIGHT, pady=Padding.BOTTOM)

        self.add('Index')
        self.add('Types')
        self.add('Date Parser')
        self.add('Converter')

        self.tab('Index').grid_columnconfigure(0, weight=1)
        self.tab('Types').grid_columnconfigure(0, weight=1)
        self.tab('Date Parser').grid_columnconfigure(0, weight=1)
        self.tab('Converter').grid_columnconfigure(0, weight=1)

        CTkLabel(self.tab('Index'), text='Enter Index:').grid(
            row=0, column=0, padx=Padding.LARGE, pady=Padding.TOP)
        index_tooltip = CTkLabel(self.tab('Index'), text='?')
        index_tooltip.grid(row=0, column=0, padx=Padding.RIGHT,
                           pady=Padding.TOP, stick=E)
        CTkTooltip(master=index_tooltip,
                   wrap_length=350,
                   delay=250,
                   text='Enter column names or index numbers.'
                   ' eg. ["foo", "bar"], or [1, 3]',
                   justify='left')
        self.index_textbox = CTkTextbox(self.tab('Index'))
        self.index_textbox.grid(row=1, column=0, sticky='nsew',
                                padx=Padding.LARGE, pady=Padding.BOTTOM)

        CTkLabel(self.tab('Converter'), text='Enter Converters:').grid(
            row=0, column=0, padx=Padding.LARGE, pady=Padding.TOP)
        converter_tooltip = CTkLabel(self.tab('Converter'), text='?')
        converter_tooltip.grid(
            row=0, column=0, padx=Padding.RIGHT, pady=Padding.TOP, stick=E)
        CTkTooltip(master=converter_tooltip,
                   wrap_length=350,
                   delay=250,
                   text='Dict of functions for converting values '
                   'in certain columns. Keys can either be integers '
                   'or column labels.\n'
                   'eg. {"foo" : ..., 1 : ...}\n\n'
                   'Values can be types.\n'
                   ' eg. {"foo": "int"}\n\n'
                   'Values can be lambda functions.\n'
                   'eg. {"bar": "lambda x: int(x)**2"}\n\n'
                   'NOTE: All strings, and lambda functions must be padded with ""'
                   ' to be read correctly. '
                   'All data is read as strings and must be converted to a numerical'
                   ' type before doing numerical operations.',
                   justify='left')

        self.converter_textbox = CTkTextbox(self.tab('Converter'))
        self.converter_textbox.grid(row=1, column=0, sticky='nsew',
                                    padx=Padding.LARGE, pady=Padding.BOTTOM)

        CTkLabel(self.tab('Types'), text='Enter type settings:').grid(
            row=0, column=0, padx=Padding.LARGE, pady=Padding.TOP)
        data_types_tooltip = CTkLabel(self.tab('Types'), text='?')
        data_types_tooltip.grid(row=0, column=0, padx=Padding.RIGHT,
                                pady=Padding.TOP, stick=E)
        CTkTooltip(master=data_types_tooltip,
                   wrap_length=350,
                   delay=250,
                   text='Enter a dict with keys of column names and'
                   ' values of parsable data types.\n'
                   'eg: {"foo": "uint16", "bar":"float64"}.\n\n'
                   'NOTE: If the text box is left blank, upon'
                   ' saving it will be filled with the automatically parsed types.',
                   justify='left')

        self.data_types_text = CTkTextbox(self.tab('Types'))
        self.data_types_text.grid(row=1, column=0, sticky='nsew',
                                  padx=Padding.LARGE, pady=Padding.BOTTOM)

        CTkLabel(self.tab('Date Parser'), text='Enter date parser settings:').grid(
            row=0, column=0, padx=Padding.LARGE, pady=Padding.TOP)
        dates_tooltip = CTkLabel(self.tab('Date Parser'), text='?')
        dates_tooltip.grid(row=0, column=0, padx=Padding.RIGHT,
                           pady=Padding.TOP, stick=E)
        CTkTooltip(master=dates_tooltip,
                   wrap_length=350,
                   delay=250,
                   text='Boolean. If True -> try parsing the index. \n\n'
                   'List of int or names. e.g. If [1, 2, 3] -> try parsing'
                   ' columns 1, 2, 3 each as a separate date column. \n\n'
                   'List of lists. e.g. If [[1, 3]] -> combine columns 1'
                   ' and 3 and parse as a single date column. \n\n'
                   'Dictionary/Hashmap, e.g. {"foo" : [1, 3]} -> parse columns'
                   ' 1, 3 as date and call result "foo"',
                   justify='left')

        self.dates_textbox = CTkTextbox(self.tab('Date Parser'))
        self.dates_textbox.grid(row=1, column=0, sticky='nsew',
                                padx=Padding.LARGE, pady=Padding.BOTTOM)


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

    def __init__(self, master: CTk, path_settings: dict, data_types: dict = {}) -> None:
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

        self.data_types = data_types
        self.path_settings = path_settings
        self.path_settings_alias = ['']
        self.path_settings_alias.extend(list(self.path_settings.keys()))

        self.path_text = StringVar()
        self.delim = StringVar(value='')
        self.names = StringVar(value=None)

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

        # create frame to input settings
        self.settings_frame = SettingsFrame(self)
        self.settings_frame.delim_entry.configure(textvariable=self.delim)

        # create frame for action buttons
        self.act_frame = ActionFrame(self)
        self.act_frame.import_button.configure(command=self.import_data)
        self.act_frame.save_fp_button.configure(command=self.save_data_frame)
        self.act_frame.save_path_button.configure(command=self.save_prep)

        # create frame for advanced options
        self.adv_frame = AdvancedSettingsFrame(self)

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
        del self.path_settings[selected]

        # change to blue
        self.file_frame.del_button.configure(
            fg_color=["gray95", "gray10"], state='disabled')
        self.selected.set('')

        self.update_path_json()

    # find file and set entry box to path
    def browse_func(self):
        filename = askopenfilename(filetypes=(
            ("CSV files", "*.csv"), ("All files", "*.*")))
        self.path_text.set(filename)

    ### add type checking ###
    # read settings and do type checkikng
    def read_form(self):
        # get path
        file_loc = self.path_text.get()  # check validity later
        col_names = self.settings_frame.col_name_entry.get()  # check validity
        rad_var = self.settings_frame.rad_var.get()  # always valid
        delim = self.delim.get() if self.delim.get() else None
        # index_str = self.settings_frame.index_entry.get(
        # ) if self.settings_frame.index_entry.get() else ''  # check validity

        index_str = self.adv_frame.index_textbox.get('0.0', 'end')
        converter_str = self.adv_frame.converter_textbox.get('0.0', 'end')
        data_type_str = self.adv_frame.data_types_text.get('0.0', 'end')
        dt_parser_str = self.adv_frame.dates_textbox.get('0.0', 'end')

        # self.data_manager.process()
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
                    data_type = {name: str(dtype)
                                 for name, dtype in ensure_dtype_objs(data_type).items()
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

        # add to zip:
        # :
        return {name: set for name, set in zip(['filepath_or_buffer', 'dtype', 'names',
                                                'header', 'sep', 'index_col',
                                                'converters', 'parse_dates'],
                                               [file_loc, data_type, names, header,
                                                delim, index, converter, dt_parser])}

    def clear_form(self):
        self.path_text.set('')
        self.delim.set('')
        if self.selected.get() != '':
            self.selected.set('')
            self.file_frame.del_button.configure(fg_color=["gray95", "gray10"],
                                                 state='disabled')

        # delete entry then activate placeholder and change rad button
        self.settings_frame.col_name_entry._entry.delete(0, END)
        self.settings_frame.col_name_entry._activate_placeholder()
        self.settings_frame.rad_var.set(0)

        # delete alias entry and activate placeholder
        self.act_frame.alias_entry._entry.delete(0, END)
        self.act_frame.alias_entry._activate_placeholder()

        # delete index entry and activate placeholder
        # self.settings_frame.index_entry._entry.delete(0, END)
        # self.settings_frame.index_entry._activate_placeholder()

        # delete adv frame entry
        self.adv_frame.index_textbox.delete('0.0', END)
        self.adv_frame.converter_textbox.delete('0.0', END)
        self.adv_frame.data_types_text.delete('0.0', END)
        self.adv_frame.dates_textbox.delete('0.0', END)

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
        settings = self.path_settings[selected]
        # settings = self.data_manager.read_settings(selected)
        self.path_text.set(settings['filepath_or_buffer'])

        # fill delim box
        delim = settings['sep']
        if delim is None:
            delim = ''
        self.delim.set(delim)

        # select radio button and fill header names
        if settings['names'] is not None:
            if settings['header'] == 0:
                self.settings_frame.rad_var.set(1)
            else:
                self.settings_frame.rad_var.set(2)
            self.settings_frame.set_columns()
            self.fill_placeholder_entry(self.settings_frame.col_name_entry,
                                        settings['names'])
        else:
            self.settings_frame.rad_var.set(0)

        # fill alias entry box
        self.fill_placeholder_entry(self.act_frame.alias_entry, selected)

        # fill index box
        # index_col = settings['index_col']
        # if index_col is None:
        #     index_col = ''
        # elif type(index_col) is str:
        #     index_col = f'"{index_col}"'

        # self.fill_placeholder_entry(self.settings_frame.index_entry, index_col)
        self.fill_textbox(self.adv_frame.index_textbox, settings['index_col'])

        # fill converter box
        self.fill_textbox(self.adv_frame.converter_textbox,
                          settings['converters'])

        # fill parser box
        self.fill_textbox(self.adv_frame.dates_textbox,
                          settings['parse_dates'])
        self.fill_textbox(self.adv_frame.data_types_text, settings['dtype'])
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

    def fill_textbox(self, textbox: CTkTextbox, text):

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
        # Change converter strings to py objects if possible
        if isinstance(settings['converters'], dict):
            settings['converters'] = self.convert(settings['converters'])

        if isinstance(settings['dtype'], dict):
            settings['dtype'] = self.convert(settings['dtype'])
        # Add dataframe to table
        # df = read_csv(**settings)
        # df.convert_dtypes(True)  # type:ignore

        try:
            self.table.model.df = read_csv(**settings)
        except Exception as e:
            # Display a custom error message along with the exception
            messagebox.showerror("Error", "An error occurred:\n\n" + str(e))
            return

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

        settings = {alias: form}
        if settings[alias]['dtype'] is None:
            dtypes = [str(dtype) for dtype in self.table.model.df.dtypes]
            columns = [name for name in self.table.model.df.columns]
            names_types = {name: dtype for name, dtype in zip(columns, dtypes)}
            settings[alias]['dtype'] = names_types
        # test
        # print([str(dtype) for dtype in self.table.model.df.dtypes])
        selected = self.selected.get()
        if selected != '':
            if alias != selected:
                del self.path_settings[selected]

        # update dict with new settings
        self.path_settings.update(settings)

        converted_types = {alias: self.read_dtypes(settings[alias]['dtype'])}

        self.data_types.update(converted_types)

        # update path settings json
        self.update_type_json()
        self.update_path_json()
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

        if overwrite == False:
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
            'header': self.last_import['header'] if self.last_import is not None else 'infer',
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
    app = CTk()
    import_win = ImportWindow(app, {})
    app.mainloop()
