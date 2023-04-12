from customtkinter import CTk, CTkButton, CTkFrame, CTkOptionMenu
from data_manager import DataManager
from padding import Padding

# from collections import Counter
"""
https://numpy.org/doc/stable/_images/dtype-hierarchy.png

num(erical)
float
int
uint

ord(inal)
uint

cat(egorical)
uint
str
unicode
obj
bool
category

time
datetime
period
timedelta
"""
# consider removing var selection dropdown
class ReadFrame(CTkFrame):

    def __init__(self, master: CTkFrame):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=0)  # type: ignore
        # add button to open import window
        self.import_button = CTkButton(
            self, text='Import New',
            fg_color='#517f47',
            hover_color='#385831'
        )
        self.import_button.grid(
            column=0, row=0,
            padx=Padding.LARGE,
            pady=Padding.TOP
        )
        # dropdown selection to pick data set
        self.data_opt = CTkOptionMenu(self)
        self.data_opt.grid(
            column=0, row=1,
            padx=Padding.LARGE,
            pady=Padding.BOTTOM
        )


# create a frame to display what regression/classification/visualization
# techniques are possible

class VerFrame(CTkFrame):

    def __init__(
        self,
        master: CTkFrame,
        type_requirements: list[str]
    ):
        super().__init__(master)


        self.grid_columnconfigure(0, weight=1)

        self.vis_buttons : dict[str, CTkButton] = {}

        for vis_type in type_requirements:
            button = CTkButton(self, text=vis_type,
                               fg_color=("gray90", "gray13"),
                               state='disabled',)
            button.grid(column=0, padx=Padding.LARGE,
                        pady=Padding.SMALL, sticky='ns')

            self.vis_buttons[vis_type] = button

        self.vis_buttons[type_requirements[0]].grid(column=0, padx=Padding.LARGE,
                                                    pady=Padding.TOP, sticky='ns')
        self.vis_buttons[type_requirements[-1]].grid(column=0, padx=Padding.LARGE,
                                                    pady=Padding.BOTTOM, sticky='ns')


class SelectData(CTkFrame):
    """
    create window where data from data file can be selected and read in
        based on selection different vis types are greyed out/disabled
    """

    # create frame to select data set from existing
    def __init__(
        self,
        master: CTk,
        # path_settings:dict,
        # data_types:dict = {},
        data_manager:DataManager,
        type_requirements:dict[str, dict] = {}
    ) -> None:

        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=0)  # type: ignore
        self.grid(sticky='nsew')

        # self.data_types = data_types
        # self.path_settings = path_settings
        self.data_manager = data_manager
        self.dtypes_count:dict

        # num = numerical, ord = ordinal, cat = categorical, time = datetime,
        # any = any of the above
        self.type_requirements = dict(sorted(type_requirements.items()))

        self.read_frame = ReadFrame(self)
        # when a data set is selected read dtypes and update buttons
        self.read_frame.data_opt.configure(command=self.read_dtypes)
        self.read_frame.grid(column=0, row=0, padx=Padding.LARGE,
                  pady=Padding.TOP)

        self.ver_frame = VerFrame(self, list(self.type_requirements.keys()))
        self.ver_frame.grid(column=0, row=1, padx=Padding.LARGE,
                  pady=Padding.BOTTOM)

    ## overhaul this and check dtypes ##
    ## ordinal vars can appear in multiple categories thus messing up the calculations##
    def update_buttons(self, required:dict[str, tuple], button:CTkButton):
        """update status of buttons to disabled or enabled if data
        type in settings matches data types in path_settings.json

        Args:
            required (dict[str, tuple]): type requirements for vis type
            button (CTkButton): button for vis type
        """
        # get counts for
        temp_types_dict = self.dtypes_count.copy()

        for v in required.values():
            num, *types = v
            if 'any' in types:
                # Check if there are enough variables of any type available
                total = sum(temp_types_dict.values())
                if total >= num:
                    # Reduce the number of variables of each type by the number required
                    for type, count in temp_types_dict.items():
                        temp_types_dict[type] = max(0, count - num)
                    break
            else:
                for type in types:
                    if type in temp_types_dict and temp_types_dict[type] >= num:
                        temp_types_dict[type] -= num
                        break
                    elif (
                        type in ('num', 'cat') and
                        'ord' in temp_types_dict and
                        temp_types_dict['ord'] >= num
                    ):
                        temp_types_dict['ord'] -= num
                        break
                else:
                    button.configure(fg_color=["gray90", "gray13"], state='disabled')
                    return None

        button.configure(state = 'normal',fg_color = ["#3a7ebf", "#1f538d"])
        return None


    def read_dtypes(self, selected):
        # TODO: Figure out why parallel is active for null selection
        # self.dtypes_count = {key:len(value)
        #                      for key, value in self.data_types[selected].items()}
        selected_dtypes = self.data_manager.load_selected_dtypes(selected).items()
        if selected_dtypes is {}:
            for button in self.ver_frame.vis_buttons.values():
                button.configure(fg_color=("gray90", "gray13"), state='disabled')
        self.dtypes_count = {
            key:len(value)
            for key, value in selected_dtypes
        }
        for text, button in self.ver_frame.vis_buttons.items():
            required = self.type_requirements[text]
            self.update_buttons(required, button)