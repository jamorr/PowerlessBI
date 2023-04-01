from tkinter import Frame, Tk
from pandastable import Table
import pandas as pd





class TestWindow(Tk):
    def __init__(self):
        super().__init__()

        self.main_frame = Frame(self)
        self.main_frame.pack(fill='both')
        self.df = pd.read_csv(r'C:/Users/Morri/Documents/Notebooks/DSCI1302/Project/winequality-red.csv', sep=';')
        # Calculate the DPI scaling factor for the display
        dpi_scale = self.winfo_screenmmwidth() / self.winfo_screenwidth()

        # Use the scaling factor to set the size of the pandastable
        pandastable_width = int(800 * dpi_scale)
        pandastable_height = int(600 * dpi_scale)
        self.table_1 = Table(self.main_frame, dataframe=self.df, showstatusbar=True, showtoolbar=True,width=pandastable_width, height=pandastable_height)
        self.table_1.show()


if __name__ == '__main__':
    test_1 = TestWindow()
    test_1.mainloop()