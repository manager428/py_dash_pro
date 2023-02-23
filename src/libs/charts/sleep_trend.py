import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime
from typing import Union
import datetime
from dateutil.relativedelta import relativedelta


class SleepTrend:
    def __init__(self, dataframe):
        self.fig = make_subplots(rows=1, cols=1, shared_xaxes=True,
                                 vertical_spacing=0.02)

        colnames=['DateTime', 'BedTime']
        if 'WakeUpTime' in dataframe:
            self.wake_up_column = 'WakeUpTime' 
        else:
            self.wake_up_column ='SleepOffset'
        colnames.append(self.wake_up_column)
        self.df = dataframe[colnames]

    @staticmethod
    def format_timedelta(x: Union[datetime.timedelta, pd.Timedelta]) -> str:
        """This function takes a timedelta and formats it to hh:mm"""
        return f'{x.components.hours:02d}:{x.components.minutes:02d}' if not pd.isnull(x) else ''

    @staticmethod
    def make_wake_relative(wake, date):
        midnight = datetime.datetime.combine(date, datetime.datetime.min.time())
        difference = wake - midnight
        if difference.days == 1 :
            return difference.total_seconds() - 86400

        return difference.total_seconds()

    @staticmethod
    def make_wake_final(row):
        if row.r_bedtime < 0 :
            return abs(row.r_bedtime)+ row.r_wakeup
        else :
            return row.r_wakeup - row.r_bedtime 

    @staticmethod
    def make_bedtime_relative(bedtime):
        midnight = datetime.datetime.combine(bedtime, datetime.datetime.min.time())
        if bedtime.hour < 12 :
            difference = bedtime - midnight
            return difference.total_seconds()
        else :
            midnight += datetime.timedelta(days=1)
            difference = midnight - bedtime
            return -difference.total_seconds() 


    @staticmethod
    def seconds_to_time(seconds, date):
        """Converts seconds relative to midnight back into a datetime using midnight on `date`"""
        return datetime.datetime.combine(date, datetime.datetime.min.time()) + datetime.timedelta(seconds=seconds)

    @staticmethod
    def datetime_to_12hr(datetime):
        """Formats a datetime into 12hr time"""
        return datetime.strftime("%I:%M %p")

    @classmethod
    def format_relative_seconds(cls, seconds, date):
        if pd.isnull(seconds):
            return ""   
        return cls.datetime_to_12hr(cls.seconds_to_time(seconds, date))   

    def clean_data(self):
        """Creates new columns of datetimes from raw sleep data"""

        self.df["date"] = pd.to_datetime(self.df["SleepOffset"], format="%Y-%m-%d")
        self.df["date_on_x"] = self.df.apply(lambda row: row.date.date(), axis=1)
        self.df["bedtime"] = pd.to_datetime(self.df['BedTime'])
        self.df["wakeup"] = pd.to_datetime(self.df[self.wake_up_column])
        self.df["sleeptime"] = self.df.apply(lambda row: pd.to_timedelta(row.wakeup-row.bedtime), axis=1)
        self.df = self.df.sort_values("date")

        # These columns represent the bedtime/wakeup in seconds relative to midnight
        self.df["r_bedtime"] = self.df.apply(lambda row: self.make_bedtime_relative(row.bedtime), axis=1)
        self.df["r_wakeup"] = self.df.apply(lambda row: self.make_wake_relative(row.wakeup, row.date), axis=1)
        self.df["final_wakeup"] = self.df.apply(lambda row: self.make_wake_final(row), axis=1)

        # Formatted seconds to midnight
        self.df["f_bedtime"] = self.df.apply(lambda row: self.format_relative_seconds(row.r_bedtime, row.date), axis=1)
        self.df["f_wakeup"] = self.df.apply(lambda row: self.format_relative_seconds(row.r_wakeup, row.date), axis=1)
        
        self.df["mean_bedtime"] = self.df["r_bedtime"].mean()
        self.df["mean_wakeup"] = self.df["r_wakeup"].mean()

    def create_traces(self):
        """Adds all the traces"""
        day_width_in_msec = 1000*3600*24/2
        self.fig.add_trace(
            go.Bar(
                name="Sleeping Hours",
                x=self.df["date_on_x"],
                base=self.df["r_bedtime"],
                y= self.df["final_wakeup"],
                width = day_width_in_msec,
                marker_color='#6B8EC7',
                customdata=np.stack(
                    (self.df.f_bedtime, self.df.f_wakeup, self.df.sleeptime.apply(self.format_timedelta)), axis=-1),
                hovertemplate="Bedtime: %{customdata[0]}<br>"
                              "Wakeup: %{customdata[1]}<br>"
                              "Total Time: %{customdata[2]}"
                              "<extra></extra>",
            )
        )

        self.fig.add_trace(
            go.Scatter(
                name="Wakeup Average",
                x=self.df["date_on_x"],
                y=self.df["mean_wakeup"],
                marker_color = '#C7887F',
                customdata=self.df.apply(lambda row: self.format_relative_seconds(row.mean_wakeup, row.date), axis=1),
                hovertemplate="Average Wakeup: %{customdata}"
                              "<extra></extra>",
            ),
            row=1, col=1
        )

        self.fig.add_trace(
            go.Scatter(
                name="Bedtime Average",
                x=self.df["date_on_x"],
                y=self.df["mean_bedtime"],
                marker_color = '#AAC758',
                customdata=self.df.apply(lambda row: self.format_relative_seconds(row.mean_bedtime, row.date), axis=1),
                hovertemplate="Average Bedtime: %{customdata}"
                              "<extra></extra>",
            ),
            row=1, col=1
        )

    def update_layout(self):
        """Updates the plots layout to change hovermode, ticks, title and theme"""
        time_range = list(range(-86400, 86400, 3600))  # All hours of the day in seconds relative to midnight
        x=self.df["date_on_x"]
        start_range = x.iloc[0] + relativedelta(days=-3)
        end_range = x.iloc[-1] + relativedelta(days=+3)
        self.fig.update_layout(
            xaxis_range=[start_range,end_range],
            title= dict(text="  <b>Consistency of Sleep and Wake-up Times</b> ", font=dict(color = '#424149',family='Roboto',size=16)),
            hovermode="x unified",
            plot_bgcolor="white",
            yaxis=dict(
                tickmode='array',
                tickvals=time_range,
                ticktext=[self.format_relative_seconds(time, datetime.datetime.today()) + "  " for time in time_range]
            ),

        )
        self.fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', 
            gridcolor='lightgray', tickvals = x, tickformat = '%d %b')
        self.fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='white')  

    def plot(self):
        """Displays the plot"""
        self.clean_data()
        self.create_traces()
        self.update_layout()
        return self.fig                   