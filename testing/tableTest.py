import ctypes
from tkinter import Tk
from customtkinter import (END, CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkOptionMenu, CTkRadioButton, E, IntVar, StringVar,
                           W, CTkTextbox, BOTH)
from pandastable import Table

root = CTk()

ctypes.windll.shcore.SetProcessDpiAwareness(2)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
frame = CTkFrame(root)
frame.grid(sticky = 'nsew')
# Calculate the DPI scaling factor for the display
dpi_scale = root.winfo_screenheight() / root.winfo_screenmmheight()


# Use the scaling factor to set the size of the pandastable
pandastable_width = int(800 * dpi_scale)
pandastable_height = int(600 * dpi_scale)

# Use the scaling factor to set the font size and row height of the pandastable
font_size = int(14 * dpi_scale)
row_height = int(20 * dpi_scale) #width=pandastable_width,height=pandastable_height


table = Table(parent = frame,showstatusbar=True,
              showtoolbar=True, **{'thefont': ('Arial',font_size), 'rowheight':row_height})


table.importCSV(r'C:/Users/Morri/Documents/Notebooks/DSCI1302/Project/Red Wine with index.csv', sep=',',
                        header=0,index_col = 0,)
table.autoResizeColumns()
table.showindex = True
table.show()


root.mainloop()