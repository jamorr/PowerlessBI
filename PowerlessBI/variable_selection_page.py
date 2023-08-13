# from time import perf_counter_ns
from typing import Tuple, Callable
# from tkinter import colorchooser

from customtkinter import (BooleanVar, CTk, CTkButton, CTkCheckBox, CTkFont,
                           CTkTabview, CTkFrame, CTkLabel, CTkOptionMenu,
                           StringVar, CTkSlider, DoubleVar, CTkSwitch, W)

from padding import Padding

"""
generate x vars on target var option select
pass in list of variables by data type
gen list of y vars that are possible given the vis type
upon selecting a y_var generate the possible x_variables based
on type and selected y_var
"""


class LeftFrame(CTkFrame):
    def __init__(self, master: CTkFrame, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)

        CTkLabel(
            self,
            text="X variable(s):",
            anchor='center'
        ).grid(
            row=0, column=0,
            padx=Padding.LARGE,
            pady=Padding.TOP,
            sticky="ew"
        )

    def add_type_option(self, **kwargs):
        self.x_type_option = CTkOptionMenu(self, **kwargs)
        self.x_type_option.grid(column=0, row=1,
                                sticky='ew',
                                padx=Padding.LARGE,
                                pady=Padding.SMALL,)

    def addCheckbox(self, check_var: BooleanVar, var_name: str, ind: int):
        checkbox = CTkCheckBox(self, text=var_name, variable=check_var,
                               onvalue=True, offvalue=False)
        checkbox.grid(column=0, row=ind,
                      sticky='ew',
                      padx=Padding.LARGE,
                      pady=Padding.SMALL,
                      stick=W)
        checkbox.grid_remove()
        return checkbox

# TODO: #12 add a tab to select format/dimensions of the plots & switch for single plot
# vs subplots


class RightFrame(CTkFrame):
    def __init__(self, master: CTkFrame, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)

    def add_y_opt(self, **kwargs):
        CTkLabel(
            self,
            text="Target variable:",
            anchor='center'
        ).grid(
            padx=Padding.LARGE,
            pady=Padding.TOP,
            sticky="ew"
        )

        self.y_option = CTkOptionMenu(self, **kwargs)
        self.y_option.grid(padx=Padding.LARGE,
                           pady=Padding.SMALL,
                           sticky="ew",)  # stick=W

    def add_check_uncheck(self, check, uncheck):
        self.uncheck = CTkButton(self, text='Clear All', command=uncheck)
        self.uncheck.grid(sticky='ew', padx=Padding.LARGE, pady=Padding.TOP)

        self.check = CTkButton(self, text='Select All', command=check)
        self.check.grid(sticky='ew', padx=Padding.LARGE, pady=Padding.SMALL)

    def add_generate(self, gen_func):
        self.gen_button = CTkButton(self, text='Generate', command=gen_func)
        self.gen_button.grid(
            sticky='ew', padx=Padding.LARGE, pady=Padding.LARGE)


class ColorFrame(CTkTabview):
    def __init__(self, master: CTkFrame):
        super().__init__(master)

        self.add('Color Palette')
        self.tab('Color Palette').grid_columnconfigure(0, weight=1)

    def add_color_var_option(self, values, variable):
        self.add('Color Variable')
        self.tab('Color Variable').grid_columnconfigure(0, weight=1)
        CTkLabel(
            self.tab('Color Variable'),
            text="Color variable:",
            anchor='center'
        ).grid(
            padx=Padding.LARGE,
            pady=Padding.TOP,
            sticky="ew"
        )
        self.color_option = CTkOptionMenu(
            self.tab('Color Variable'),
            values=values,
            variable=variable
        )
        self.color_option.grid(padx=Padding.LARGE,
                               pady=Padding.SMALL,
                               sticky="ew")

    def add_opacity_tab(self):
        self.add('Opacity')
        self.tab('Opacity').grid_columnconfigure(0, weight=1)

        self.auto_opacity = BooleanVar(value=True)
        self.opacity = DoubleVar(value=0)

        self.auto_opacity_switch = CTkSwitch(
            self.tab('Opacity'),
            text="Auto-Opacity",
            variable=self.auto_opacity,
            command=self.toggle_opacity_slider
        )
        self.auto_opacity_switch.grid(
            row=0, column=0,
            padx=Padding.LARGE,
            pady=Padding.TOP
        )

        self.opacity_slider = CTkSlider(
            self.tab('Opacity'),
            variable=self.opacity,
            state='disabled'
        )
        self.opacity_slider.grid(
            row=1, column=0,
            padx=Padding.LARGE,
            pady=Padding.BOTTOM
        )

    # TODO: #7 add a color picker
    def add_color_picker(self):

        pass

    def toggle_opacity_slider(self, *args):
        new_state = 'normal' if self.opacity_slider.cget('state') == 'disabled'\
            else 'disabled'
        self.opacity_slider.configure(state=new_state)


class VarWindow(CTkFrame):
    def __init__(
        self,
        master: CTk,
        vis_type: str,
        var_list: dict[str, list[str]] = {},
        type_requirements: dict[str, Tuple[int, str]] = {},
        home_func: Callable | None = None,
        gen_func: Callable | None = None
    ):
        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)  # type: ignore
        # self.grid_columnconfigure(2, weight=0)

        self.vis_type = vis_type
        self.var_list = var_list
        self.type_requirements = type_requirements

        self.last_selected_x_type: str = ''
        self.x_type = StringVar()

        self.last_selected_y: str = ''
        self.selected_y_var = StringVar()
        self.selected_color_var = StringVar()

        self.add_check_uncheck = False

        self.x_vars: list[str]
        self.y_var: list[str] = self.check_required(
            self.type_requirements['y'])
        self.color_vars: list[str] = self.check_required(
            self.type_requirements['c'])

        self.left_frame = LeftFrame(self)
        self.right_frame = RightFrame(self)

        self.left_frame.grid(
            row=1, rowspan=2,
            column=0, sticky='nsew',
            ipady=Padding.SMALL, ipadx=Padding.LARGE,
            padx=Padding.LEFT, pady=Padding.BOTTOM
        )
        self.right_frame.grid(
            row=1, rowspan=2,
            column=1, sticky='nsew',
            padx=Padding.RIGHT,
            pady=Padding.BOTTOM
        )

        header_font = CTkFont(family=None, size=20,
                              weight="bold", slant="roman")
        CTkLabel(
            self, text=self.vis_type,
            font=header_font, anchor='center'
        ).grid(
            row=0, column=0,
            columnspan=2,
            padx=Padding.LARGE,
            pady=Padding.TOP,
            sticky="ew"
        )

        self.home_button = CTkButton(
            self, width=28, text='⌂',
            text_color='black',
            fg_color='#517f47',
            hover_color='#385831',
            command=home_func
        )
        self.home_button.grid(
            row=0, column=0, padx=Padding.LEFT,
            pady=Padding.TOP, sticky="ns", stick=W
        )

        gen = getattr(self, 'gen_' + '_'.join(vis_type.lower().split(' ')))
        gen()

        self.add_buttons(gen_func)

    def check_required(self, type_reqs: tuple[int, str]) -> list[str]:
        temp_types_dict = self.var_list.copy()
        num, *types = type_reqs
        out = []
        if 'any' in types:
            for names_list in temp_types_dict.values():
                out.extend(names_list)
            return out

        for type in types:
            if type in temp_types_dict:
                out.extend(temp_types_dict[type])

            elif type in ('num', 'cat') and 'ord' in temp_types_dict:
                out.extend(temp_types_dict['ord'])

        return out

    def add_buttons(self, gen_func):
        if self.add_check_uncheck:
            self.right_frame.add_check_uncheck(
                self.check_all, self.uncheck_all)
        self.right_frame.add_generate(gen_func)

    def check_all(self):
        for box in self.x_checkboxes.values():
            box[1].select()

    def uncheck_all(self):
        for box in self.x_checkboxes.values():
            box[1].deselect()

    # generate a checkbox for all possible x vars
    # add checkbox to grid if of the correct type otherwise remove from grid
    # in the future may add functionality to select multiple x types?
    def gen_x_vars(self, x_type: str = ''):
        selected_y_var = self.selected_y_var.get()
        if self.last_selected_x_type == '':
            # create dict of possible X vars by type
            number, *types = self.type_requirements['X']
            x_dict: dict[str, list[str]] = {}

            for type_req in types:
                x_dict[type_req] = self.check_required((number, type_req))

            self.x_dict = x_dict

            # create option menu to select type and set current val
            self.x_type.set(types[0])
            x_type = types[0]

            self.left_frame.add_type_option(
                values=list(x_dict.keys()),
                variable=self.x_type,
                command=self.gen_x_vars
            )

            self.x_checkboxes: dict[str, tuple[BooleanVar, CTkCheckBox]] = {}
            x_vars = self.check_required(self.type_requirements['X'])
            self.add_checkboxes(x_vars)  # adds checkboxes to self.x_checkboxes

            # self.x_checkboxes[list(self.x_checkboxes.keys())[-1]][1].grid(pady=Padding.BOTTOM)
            self.add_check_uncheck = True

        if (self.last_selected_x_type != x_type) or \
                (selected_y_var != self.last_selected_y):
            for var, checkbox in self.x_checkboxes.values():
                checkbox.grid_remove()

            temp = self.x_dict[x_type].copy()
            try:
                temp.remove(selected_y_var)
            except ValueError:
                pass

            for var in temp:
                self.x_checkboxes[var][1].grid()

            # only allows check if x_type is different from last time
            self.last_selected_x_type = x_type
            # pass this to main to get selected x-vars
            # excludes selected x-vars that arent visible (y var or wrong type)
            self.selectable_x_vars = temp

        if selected_y_var != '':
            self.last_selected_y = selected_y_var

    def gen_x_options(self, var_list):

        if self.x_checkboxes_bool is False:
            self.x_options: list[tuple[StringVar, CTkOptionMenu]] = var_list

    def add_checkboxes(self, var_list):
        for ind, var in enumerate(var_list):
            bool_var = BooleanVar()
            checkbox = self.left_frame.addCheckbox(bool_var, var, ind + 2)
            self.x_checkboxes[var] = (bool_var, checkbox)

    def gen_y_vars(self, command: Callable | None = None):
        """generate y variables based on requirements
        """
        if command is None:
            command = (lambda _: self.gen_x_vars(self.x_type.get()))  # noqa: E731
        self.right_frame.add_y_opt(
            values=self.y_var,
            variable=self.selected_y_var,
            # regen x vars based on chosen y_var
            command=command)
        self.selected_y_var.set(self.y_var[0])
        self.last_selected_y = self.y_var[0]
        self.x_checkboxes_bool = True

    def gen_color(self):
        self.right_frame.grid_configure(rowspan=1)
        self.color_frame = ColorFrame(self)
        self.color_frame.add_color_var_option(
            self.color_vars, self.selected_color_var)
        self.color_frame.add_color_picker()
        self.color_frame.add_opacity_tab()
        self.color_frame.grid(
            row=2, column=1,
            sticky='nsew',
            padx=Padding.RIGHT,
            pady=Padding.BOTTOM
        )

    def gen_scatter(self):
        self.gen_y_vars()
        self.gen_x_vars()
        self.gen_color()

    def gen_violin(self):
        self.gen_y_vars()
        self.gen_x_vars()
        self.gen_color()

    def gen_ridgeline(self):
        self.gen_y_vars()
        self.gen_x_vars()
        self.gen_color()

    def gen_parallel(self):
        self.gen_x_vars()
        self.gen_color()

    def gen_histogram(self):
        self.gen_x_vars()
        self.gen_color()

    def gen_statistics(self):
        self.gen_x_vars()

    def gen_linear_regression(self):
        self.gen_y_vars()
        self.gen_x_vars()
        self.gen_color()

    def gen_scatter_3d(self):
        self.gen_y_vars(command=self.gen_x_options)
        self.x_checkboxes_bool = False
        self.gen_x_options([])
        self.gen_color()

    def gen_line(self):
        # change labels to show that you pick multiple ys and one x
        # change master
        self.gen_y_vars()
        self.gen_x_vars()
        self.gen_color()

    def get_selected_vars(self):
        x_vars = [var for var, tup in self.x_checkboxes.items()
                  if tup[0].get() is True and var in self.selectable_x_vars]
        # check if x_vars are showing
        y_var = self.selected_y_var.get()
        if (color := self.selected_color_var.get()) == '':
            color = None
        vis_type = "_".join(self.vis_type.lower().split(' ')) + "_plot"
        return x_vars, y_var, color, vis_type


if __name__ == '__main__':
    app = CTk()
    app.grid_columnconfigure(0, weight=1)
    import_win = VarWindow(app, 'Violin',
                           {"cat": [
                               "quality"
                           ],
                               "num": [
                               "alcohol",
                               "chlorides",
                               "citric acid",
                               "density",
                               "fixed acidity",
                               "free sulfur dioxide",
                               "pH",
                               "residual sugar",
                               "sulphates",
                               "total sulfur dioxide",
                               "volatile acidity"
                           ],
                               "ord": [
                               "quality"
                           ],
                               "time": []},
                           {'X': (1, 'num'),
                               'y': (1, 'ord'),
                               'c': (0, 'any')})
    import_win.grid()

    app.mainloop()
