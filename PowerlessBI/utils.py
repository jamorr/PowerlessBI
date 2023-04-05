from typing import Any, Callable
from customtkinter import (CTkFrame, CTk, CTkButton)
from padding import Padding

# make a class to hold up/ down buttons
class UpDownButtons(CTkFrame):
    def __init__(
        self,
        master: CTkFrame | CTk | Any,
        up_command: None | Callable = None,
        down_command: None | Callable = None,
        shift_up_command: None | Callable = None,
        shift_down_command: None | Callable = None,
        disable_up: bool = False,
        disable_down: bool = False,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure((0, 1), weight=0)  # type: ignore
        self.up_button = CTkButton(
            self,
            text="↑",
            width=28,
            command=up_command,
        )
        self.up_button.grid(
            row=0, column=0,
            padx=Padding.SMALL_LEFT,
            pady=Padding.SMALL,
            sticky="nsew"
        )

        self.down_button = CTkButton(
            self,
            text="↓",
            width=28,
            command=down_command,
        )
        self.down_button.grid(
            row=0, column=1,
            padx=Padding.SMALL_RIGHT,
            pady=Padding.SMALL,
            sticky="nsew"
        )

        if disable_up:
            self.disable_up()
        if shift_up_command:
            self.up_button.bind("<Shift-Button-1>", self.shift_up)
            self.shift_up_command = shift_up_command

        if disable_down:
            self.disable_down()
        if shift_down_command:
            self.down_button.bind("<Shift-Button-1>", self.shift_down)
            self.shift_down_command = shift_down_command

    def shift_up(self, event=None):
        if self.up_button.cget("state") != 'disabled':
            self.shift_up_command()

    def shift_down(self, event=None):
        if self.down_button.cget("state") != 'disabled':
            self.shift_down_command()

    def activate_up(self):
        if self.up_button.cget("state") == 'disabled':
            self.up_button.configure(state='normal')

    def activate_down(self):
        if self.down_button.cget("state") == 'disabled':
            self.down_button.configure(state='normal')

    def disable_up(self):
        if self.up_button.cget("state") == 'normal':
            self.up_button.configure(state='disabled')

    def disable_down(self):
        if self.down_button.cget("state") == 'normal':
            self.down_button.configure(state='disabled')

    def toggle_up(self):
        if self.up_button.cget("state") == 'normal':
            self.up_button.configure(state='disabled')
        else:
            self.up_button.configure(state='normal')

    def toggle_down(self):

        if self.down_button.cget("state") == 'normal':
            self.down_button.configure(state='disabled')
        else:
            self.down_button.configure(state='normal')


if __name__ == '__main__':
    app = CTk()
    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(0, weight=1)
    UpDownButtons(app).grid()
    # app.geometry("70x100+0+0")

    app.mainloop()
