from math import sqrt
from typing import Callable, Literal

import customtkinter

# import matplotlib.pyplot as plt
# import seaborn as sns
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from customtkinter import CTk, CTkFrame, CTkToplevel
from pandastable import Table
from plotly.subplots import make_subplots

"""allow creation of a large subplot then adding
different plots to it before showing it"""
# add to figure option? add subplots one at a time to the figure
# title format is title for individual subplots
# opacity - autocalculate based on density? ++ slider option
# auto-reformat subplots to be more aesthetic eg.
# [] [] -> [] [] or [] [] []
# []        []
# maybe double number of colums so that its easier to recenter later?
class PlotData:
    def __init__(self,
                 x_vars:list[str],
                 y_var:str,
                 color:str|list[str]|None,
                 vis_type:str,
                 data_frame:pd.DataFrame,
                 scale:Literal['minmax','standard']|None = None,
                 dimensions:tuple[int,int]|None = None,
                 opacity:int|Literal['infer']|None = None,
                 title_format:str = "{x} by {y}",
                 main_title:str = "",
                 master:CTk|None = None):
        # https://plotly.com/python/interactive-html-export/
        self.main_title = main_title
        self.opacity = opacity
        self.scale = scale
        self.x_vars:list[str] = x_vars
        self.y_var = y_var
        self.color = color
        # self.vis_type:str = vis_type
        self.data_frame:pd.DataFrame = data_frame
        self.dims = self.nearest_rectangle() if dimensions is None else dimensions
        self.title_format = title_format
        self.master = master
        plot = getattr(self, vis_type)
        plot()

    def plot_subplots(self, shared_y:bool, shared_x:bool, add_type_trace:Callable):
        # create subplots and titles
        subplot_titles = [self.title_format.format(x = x_var, y = self.y_var)
                          for x_var in self.x_vars]
        fig = make_subplots(rows=self.dims[0],
                            cols=self.dims[1],
                            shared_yaxes=shared_y,
                            shared_xaxes=shared_x,
                            subplot_titles=subplot_titles
                            )
        # Create a plot for each index of the figure
        index = np.ndarray(shape = self.dims)
        for ind, _ in np.ndenumerate(index):
            ind_x = ind[0] * self.dims[1] + ind[1]
            if ind_x == len(self.x_vars):
                break

            x_var = self.x_vars[ind_x]
            add_type_trace(fig, x_var, ind)

            # Configure Axes titles
            if shared_y and ind[1] == 0:
                fig.update_yaxes(row = ind[0]+1, col = ind[1]+1,
                                 title_text = f"{self.y_var}")
            elif shared_y is False:
                fig.update_yaxes(row = ind[0]+1, col = ind[1]+1,
                                 title_text = f"{self.y_var}")


            fig.update_xaxes(row = ind[0]+1, col = ind[1]+1, title_text = f"{x_var}")


        fig.update_layout(showlegend=False)
        fig.show()

    def scatter_plot(self):
        self.plot_subplots(True, False, self.add_scatter_trace)

    def add_scatter_trace(self, fig, x_var, ind):
        fig.add_trace(go.Scatter(x = self.data_frame[x_var],
                                     y = self.data_frame[self.y_var],
                                     mode='markers'),
                          row = ind[0]+1, col=ind[1]+1)

    def histogram_plot(self):
        if self.title_format == "{x} by {y}":
            self.title_format = "Frequency of {x}"
        self.plot_subplots(True, False, self.add_histogram_trace)

    def add_histogram_trace(self, fig:go.Figure, x_var:str, ind:tuple):
        fig.add_trace(go.Histogram(x = self.data_frame[x_var]),
                          row = ind[0]+1, col=ind[1]+1,)

    def violin_plot(self):
        self.unique_categories = self.data_frame[self.y_var].unique()
        self.plot_subplots(True, False, self.add_violin_traces,)

    def add_violin_traces(self, fig:go.Figure, x_var:str, ind:tuple):
        y_var = self.y_var
        for group in self.unique_categories:
            fig.add_trace(
                go.Violin(
                    x = self.data_frame[y_var][self.data_frame[y_var]==group],
                    y = self.data_frame[x_var][self.data_frame[y_var]==group]),
                row = ind[0]+1, col=ind[1]+1
            )
        #box_visible=True,
        # fig.update_layout(showlegend=False, meanline_visible=True)


    def ridgeline_plot(self):
        self.unique_categories = self.data_frame[self.y_var].unique()
        self.plot_subplots(True, False, self.add_ridgeline_traces)

    def add_ridgeline_traces(self, fig:go.Figure, x_var:str, ind:tuple):
        y_var = self.y_var
        for group in self.unique_categories:
                fig.add_trace(
                    go.Violin(
                        y = self.data_frame[y_var][self.data_frame[y_var]==group],
                        x = self.data_frame[x_var][self.data_frame[y_var]==group]),
                    row = ind[0]+1, col=ind[1]+1
                )

        fig.update_traces(orientation='h', side='positive',width=3, showlegend = False)




    def line_plot(self):
        fig = px.scatter(data_frame=self.data_frame, x = self.x_vars, y=self.y_var)
        fig.show()

    def parallel_plot(self):
        """add option for only categorical variables/only numerical
        sort order of lines by mean/std from least to greatest"""
        fig = px.parallel_coordinates(data_frame=self.data_frame,
                                      dimensions = self.x_vars,
                                      color=self.color,)
        # if self.color == None:
        #     color = None
        # else:
        #     color = self.data_frame[self.color]

        # fig = go.Figure(
        #     line = dict(color = color),
        #     data=go.Parcoords(dimensions = self.data_frame[self.x_vars]))
        fig.show()
        # plot.write_html(f"{self.save_path}/parallel-plot-{self.x_vars}.html")


    def correlation_chart(self):



        pass

    def statistics_plot(self):
        df = self.data_frame[self.x_vars]
        sum_stats = df.describe().T
        sum_stats['median'] = [df[f'{col}'].median() for col in df]
        sum_stats['variance'] = [df[f'{col}'].var() for col in df]
        sum_stats = sum_stats[['mean','median','variance', 'std',
                               'min', '25%', '50%', '75%', 'max']].convert_dtypes(True)

        app = CTkToplevel(self.master)
        app.grid_columnconfigure(0,weight=1)
        app.grid_rowconfigure(0,weight=1)
        frame = CTkFrame(app)
        frame.grid(sticky = 'nsew')
        dpi_scale = customtkinter.ScalingTracker.get_window_dpi_scaling(app)

        # Use the scaling factor to set the font size and row height of the pandastable
        font_size = int(14 * dpi_scale)  # type:ignore
        row_height = int(20 * dpi_scale)  # type:ignore

        # assign font size and row height with kwargs and construct table
        table:Table = Table(parent=frame,
                    #showstatusbar=True,showtoolbar=True,
                    **{'thefont': ('Arial', font_size),
                        'rowheight': row_height})
        table.model.df = sum_stats
        table.showindex = True
        table.autoResizeColumns()
        table.show()

    def scatter_3d_plot(self):



        pass

    def meshgrid_3d_plot(self):
        pass



    def estimate_opacity(self):
        # colorrgba(rr,gg,bb,a) a is alpha or opacity


        pass


    def nearest_rectangle(self) -> tuple[int, int]:
        num_vars = len(self.x_vars)
        length = width = round(sqrt(num_vars))

        if length * width < num_vars:
            width += 1

        return length, width

if __name__ == "__main__":
    settings = {
        "converters": None,
        "dtype": {
            "alcohol": "float64",
            "chlorides": "float64",
            "citric acid": "float64",
            "density": "float64",
            "fixed acidity": "float64",
            "free sulfur dioxide": "float64",
            "pH": "float64",
            "quality": "uint8",
            "residual sugar": "float64",
            "sulphates": "float64",
            "total sulfur dioxide": "float64",
            "volatile acidity": "float64"
        },
        "filepath_or_buffer":
            "C:/Users/Morri/Documents/Notebooks/DSCI1302/Project/winequality-red.csv",
        "header": 0,
        "index_col": None,
        "names": None,
        "parse_dates": False,
        "sep": ";"
    }
    data_frame = pd.read_csv(**settings)
    PlotData(['sulphates', 'chlorides', 'citric acid'],
             'quality', None, 'violin_plot', data_frame=data_frame)

