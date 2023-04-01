from customtkinter import (CTkFrame, CTkCanvas, CTkScrollbar,
                           CTkBaseClass,ThemeManager, DrawEngine,
                           LEFT, RIGHT, FALSE, X, Y, BOTH, TRUE, NW)


### fix issues with resizing upon scroll/resizing on min/maximize ###
class ScrolledFrame(CTkFrame):
    """A pure Tkinter scrollable frame \
    see http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame. \
    Use the 'interior' attribute to place widgets inside the scrollable frame.
    """

    def __init__(self, parent, height=None, width=None, corner_radius = None, *args, **kw):

        CTkFrame.__init__(self, parent, *args, **kw)
        self.grid_columnconfigure(0, weight=1)

        self._fg_color = ThemeManager.theme["CTkFrame"]["top_fg_color"]
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = CTkScrollbar(self, fg_color=self._fg_color)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)

        self._canvas = CTkCanvas(self, bd=0, highlightthickness=0,
                                background = self._fg_color[1], height=height,
                                width=width, yscrollcommand=vscrollbar.set)
        self._canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        # canvas.delete("background_parts")
        vscrollbar.configure(command=self._canvas.yview)

        # reset the view
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        # fg_color = self.fg_color?


        self.interior = interior = CTkFrame(self._canvas, fg_color=self._fg_color)


        self.interior_id = self._canvas.create_window((0, 0), window=interior,
                                                     anchor = 'nw'
                                                     )

        # needed to draw rounded corners
        self._draw_engine = DrawEngine(self._canvas)
        # self._draw_engine.draw_rounded_rect_with_border()
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius

        self.interior.bind('<Configure>', self._configure_interior)
        self._canvas.bind('<Configure>', self._configure_canvas)
        self.bind('<Configure>', self._configure_interior, add=True)
        self.bind('<Configure>', self._configure_canvas, add=True)

        self._canvas.bind_all('<Map>', self._bind_new_widget, add=True)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_touchpad(self, event):
        self._canvas.yview_scroll(-1*event.y, "units")

    def _bind_new_widget(self, event):
        try:
            parents = event.widget.winfo_parent().split('.')[1:]
        except:
            return
        for parent in parents:
            if parent == self.winfo_name(): #, self.interior.winfo_name(), self._canvas.winfo_name()]
                event.widget.bind("<B2-Motion>", self._on_touchpad)
                event.widget.bind("<MouseWheel>", self._on_mousewheel)
                return

    # track changes to the canvas and frame width and sync them,
    # also updating the scrollbar
    def _configure_interior(self, event):
        # update the scrollbars to match the size of the inner frame
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self._canvas.configure(scrollregion=(0, 0, size[0], size[1]))
        if self.interior.winfo_reqwidth() != self._canvas.winfo_width():
            # update the canvas's width to fit the inner frame
            self._canvas.configure(width=self.interior.winfo_reqwidth())

    # bug: this makes it too small when enabled and scrolling, and too small when disabled and screen size changes
    def _configure_canvas(self, event):
        if self.interior.winfo_reqwidth() != self._canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            self._canvas.itemconfigure(self.interior_id, width=self._canvas.winfo_width())


from typing import Optional, Union, Tuple

from customtkinter import CTkFrame,CTkScrollbar,CTkCanvas,AppearanceModeTracker
# from .core_rendering import CTkCanvas
# from .ctk_scrollbar import CTkScrollbar
# from .ctk_frame import CTkFrame
# from .appearance_mode import AppearanceModeTracker


class CTkScrollableFrame(CTkFrame):
    """
    A scrollable frame that allows you to add any kind of items (including frames with multiple widgets on it).
    all you have to do is inherit from this class. Example
    parent_scrollable = customtkinter.ScrollableFrame(parent)
    item = customtkinter.CTkFrame(master=parent_scrollable.scrollable_frame)
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.canvas = CTkCanvas(self, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nswe")
        self.canvas.grid_rowconfigure(0, weight=1)
        self.canvas.grid_columnconfigure(0, weight=1)

        self.update_canvas_color()

        self.scrollbar = CTkScrollbar(self, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="nswe")

        self.scrollable_frame = CTkFrame(self.canvas, width=60000, height=50000) #scrollable frame is invisible. assuming it was stretched at max, the scroll upwards bug wont happen
        self.scrollable_frame.configure(fg_color='transparent')

        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.update_scrollable_frame_color()

        self._frame_id = self.canvas.create_window(0, 0, window=self.scrollable_frame,)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<Configure>", self.resize_frame)  # increase the items inside the canvas as the canvas grows

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.bind('<Enter>', lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind('<Leave>', lambda e: self.canvas.unbind_all('<MouseWheel>'))


    def resize_frame(self, e):
        self.canvas.itemconfig(self._frame_id, height=None,
                               width=e.width)  # height = None because otherwise wont scroll

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # self.canvas.yview_moveto(int(-1 * (event.delta / 120)))

    def get_appearance_mode(self) -> str:
        """ get current state of the appearance mode (light or dark) """
        if AppearanceModeTracker.appearance_mode == 0:
            return "Light"
        elif AppearanceModeTracker.appearance_mode == 1:
            return "Dark"
    def update_canvas_color(self):
        # because for some reason, Ctk canvas do not update automatically
        if self.get_appearance_mode() == "Light":
            self.canvas.configure(bg="#ffffff")
        if self.get_appearance_mode() == "Dark":
            self.canvas.configure(bg="#343638")

    def update_scrollable_frame_color(self):
        if self.get_appearance_mode() == "Light":
            self.scrollable_frame.configure(bg_color="#ffffff")
        if self.get_appearance_mode() == "Dark":
            self.scrollable_frame.configure(bg_color="#343638")




if __name__ == '__main__':
    from customtkinter import CTkButton, CTkLabel, CTk
    app = CTk()
    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(0, weight=1)
    # app.geometry("70x100+0+0")

    scrolled = CTkScrollableFrame(app)
    # scrolled.pack()
    scroll_frame = CTkFrame(scrolled.scrollable_frame)
    scroll_frame.grid_columnconfigure(0, weight=1)
    for i in range(50):
        if i%2 == 0:
            CTkButton(scroll_frame, text = str(i)).grid()
        else:
            CTkLabel(scroll_frame, text = str(i)).grid()
    scrolled.grid()
    app.mainloop()


