from ctk_tooltip import CTkTooltip
from padding import Padding
from customtkinter import (END, CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkOptionMenu, CTkRadioButton, CTkTextbox, E, W,
                           IntVar, StringVar, ScalingTracker, CTkInputDialog,
                           CTkTabview, BooleanVar, CTkScrollableFrame, CTkSwitch)

"""
Parse names for each column name
Add dropdowns to select data types for each column name
Add switches to select if a column is an index column
Add drop downs/format textboxes for date time

x <Col name> <dtype> <index> <datetime>
"""


class AdvancedSettingsFrame(CTkScrollableFrame):
    def __init__(self, master: CTkFrame):
        super().__init__(master)
        self.grid_configure(column=5, rows=3)
        # self.grid_rowconfigure(0, weight=1)
        # self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        self.rows:list[SettingsRow] = []
        self.del_buttons:list[CTkButton] = []

        self.last_row_index = 2

        self.grid(row=2, rowspan=2, column=1, sticky='nsew',
                  padx=Padding.RIGHT, pady=Padding.BOTTOM)
        CTkLabel(
            self,
            text="Advanced Settings"
        ).grid(
            row=0,
            columnspan=5,
            sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=28,
            text=''
        ).grid(
            row=1,column = 1,
            sticky="nsew",
            padx=Padding.SMALL, pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=140,
            text="Column Name"
        ).grid(
            row=1, column=1, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=36,
            text="Index"
        ).grid(
            row=1, column=2, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=140,
            text="Data Type"
        ).grid(
            row=1, column=3, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )
        CTkLabel(
            self,
            width=140,
            text="Date Time"
        ).grid(
            row=1, column=4, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )
        self.new_row_button = CTkButton(self, text="+", command=self.add_row)
        self.new_row_button.grid(row=2, column=1)



        return

    def add_row(self, name: str | None = None):
        """add a row to grid

        Args:
            name (str|None, optional): Name for new row. Defaults to None.
        """
        self.grid_rowconfigure(self.last_row_index+2)
        self.rows.append(SettingsRow(self, self.last_row_index, name))
        self.last_row_index += 1
        self.new_row_button.grid(row=self.last_row_index)

        return

    def get_settings(self):
        names = []
        indices = []
        data_types = []
        datetime = []

        for i,row in enumerate(self.rows):
            names.append(row.name.get())
            indices.append(row.is_index.get())
            data_types.append(row.data_type.get())
            datetime.append(row.date_time.get())

        return {"names":names,
                "indices":indices,
                "dtypes":data_types,
                "datetime":datetime}


class SettingsRow(CTkFrame):
    def __init__(self, master, row_num: int, name: str | None = None):
        super().__init__(master)
        self.grid(column=0, row=row_num, columnspan=5, sticky='nsew')
        # self.grid_configure(column=5, row = 1)

        self.row_num = row_num  # might not need this
        self.name = StringVar(value=name)
        self.is_index = BooleanVar()
        self.data_type = StringVar()
        self.date_time = StringVar()

        self.del_button = CTkButton(self,
                                    width=28, text="x",
                                    command=self.del_row
                                    )
        self.del_button.grid(
            column=0, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.name_entry = CTkEntry(
            self, placeholder_text="Enter Column Name", textvariable=self.name)
        self.name_entry.grid(
            column=1, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.index_switch = CTkSwitch(
            self, width=36, variable=self.is_index, text="")
        self.index_switch.grid(
            column=2, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.data_type = CTkOptionMenu(
            self, values='', variable=self.data_type)
        self.data_type.grid(
            column=3, row=0, sticky='nsew', padx=Padding.SMALL, pady=Padding.SMALL
        )

        self.date_time = CTkEntry(
            self, placeholder_text="Enter DateTime Format", textvariable=self.date_time)
        self.date_time.grid(
            column=4, row=0,
            sticky="nsew",
            padx=Padding.SMALL,
            pady=Padding.SMALL
        )

    def del_row(self):
        self.grid_forget()
        del self


if __name__ == '__main__':
    app = CTk()
    parent = CTkFrame(app)
    parent.grid()
    window = AdvancedSettingsFrame(parent)
    app.mainloop()
