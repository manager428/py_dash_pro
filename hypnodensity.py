import plotly.graph_objects as go
import numpy as np
import datetime
import pandas as pd

from utilities.sleep_stagings import ThreeClassLabel, FourClassLabel


class Hypnodensity:

    @staticmethod
    def __merge_for_x_display(true_labels, predicted_labels, epochs_time, timezone):
        merged_labels = []
        int_label_dict = {0: 'wake', 1: 'nrem', 2: 'rem_'}
        for t, p, i in zip(true_labels, predicted_labels, epochs_time):
            d = datetime.datetime.fromtimestamp(i + timezone)
            merged_labels.append(str(t) + '_' + int_label_dict[p] + '_' + d.strftime('%H:%M:%S'))
        return merged_labels

    @staticmethod
    def time_conversion(epochs_time, time_zone):
        time_labels = []
        for t in epochs_time:
            time_labels.append(datetime.datetime.fromtimestamp(t + time_zone))
        return time_labels     

    @staticmethod
    def __get_list_of_string_labels(num_sleep_stages):
        names = []
        if num_sleep_stages == len(ThreeClassLabel):
            names = [ThreeClassLabel(i).name for i in range(num_sleep_stages)]
        elif num_sleep_stages == len(FourClassLabel):
            names = [FourClassLabel(i).name for i in range(num_sleep_stages)]
        return names

    @classmethod
    def disply(cls, sleep_staging_result, classifier_name, time, timezone, multi_day_row):
        
        prediction = sleep_staging_result.prediction_dict[classifier_name]
        class_probabilities = prediction.probability
        predicted_labels = prediction.predicted_labels
        true_labels = sleep_staging_result.true_labels
        subject_id = sleep_staging_result.subject_id
        x = cls.time_conversion(time, timezone)
        
        range_start = x[0].replace(minute=0, second=0)
        range_end = x[-1]
        time_range = pd.date_range(range_start, range_end , freq='H')

        num_sleep_stages = len(class_probabilities[0])

        names = cls.__get_list_of_string_labels(num_sleep_stages)
        colors = ['#2CC8C1', '#779EDE', '#1B1464', 'rgb(31, 61, 122)', 'green']
        fig = go.Figure(
            go.Bar(x=x, y=list(np.array(class_probabilities)[:, 0]), name=names[0].title(), marker_color=colors[0],
                   marker_line_color=colors[0]))
        for index in range(1, num_sleep_stages):
            fig.add_trace(go.Bar(x=x, y=list(np.array(class_probabilities)[:, index]), name=names[index].upper(),
                                 marker_color=colors[index],
                                 marker_line_color=colors[index]))

        for time in time_range.tolist()[1:]:
            fig.add_shape(type="line",
            x0=time, y0=0, x1=time, y1=1,
            line=dict(
                color="#808080",
                width=0.5,
                dash="dot",
            )
        )

        try:
            fig.add_annotation(
                x=multi_day_row['BedTime'],y=1, xref="x", yref="y domain",
                text="BedTime",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)
            fig.add_annotation(
                x=multi_day_row['OutOfBedTime'],y=1, xref="x", yref="y domain",
                text="OutOfBedTime",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)
            fig.add_annotation(
                x=multi_day_row['SleepOnset'],y=0.5, xref="x", yref="y domain",
                text="SleepOnset",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)
            fig.add_annotation(
                x=multi_day_row['SleepOffset'],y=0.5, xref="x", yref="y domain",
                text="SleepOffset",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)            
        except Exception as e:
               pass        
     

        fig.update_layout(xaxis=dict(dict(type='date' )),
            yaxis=dict(showticklabels=False),
            showlegend=False,
            plot_bgcolor='white')
        fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', showticklabels=True)    
        fig.update_xaxes(showgrid=False, zeroline=True,linewidth=1, linecolor='#898989',tickformat= '%H:%M') 
        fig.update_layout(xaxis_tick0 = range_start, xaxis_dtick=3600000,xaxis_range=[range_start,range_end],)
        return fig

    @classmethod
    def display(cls, df_staging, timezone, multi_day_row):
        
        def get_time(row):
            return float(row['SK'].split('#')[2])
        df_staging['time'] = df_staging.apply(lambda row: get_time(row), axis=1)

        x = cls.time_conversion(df_staging['time'], timezone)
        
        range_start = x[0].replace(minute=0, second=0)
        range_end = x[-1]
        time_range = pd.date_range(range_start, range_end , freq='H')

        names = cls.__get_list_of_string_labels(3)
        colors = ['#2CC8C1', '#779EDE', '#1B1464', 'rgb(31, 61, 122)', 'green']
        fig = go.Figure(
            go.Bar(x=x, y=df_staging['wake_prob'], name=names[0].title(), marker_color=colors[0],
                   marker_line_color=colors[0]))
        
        fig.add_trace(go.Bar(x=x, y=df_staging['rem_prob'], name=names[1].upper(),
                                 marker_color=colors[1],
                                 marker_line_color=colors[1]))
        fig.add_trace(go.Bar(x=x, y=df_staging['nrem_prob'], name=names[2].upper(),
                                 marker_color=colors[2],
                                 marker_line_color=colors[2]))    

        for time in time_range.tolist()[1:]:
            fig.add_shape(type="line",
            x0=time, y0=0, x1=time, y1=1,
            line=dict(
                color="#808080",
                width=0.5,
                dash="dot",
            )
        )

        try:
            fig.add_annotation(
                x=multi_day_row['BedTime'],y=1, xref="x", yref="y domain",
                text="BedTime",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)
            fig.add_annotation(
                x=multi_day_row['OutOfBedTime'],y=1, xref="x", yref="y domain",
                text="OutOfBedTime",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)
            fig.add_annotation(
                x=multi_day_row['SleepOnset'],y=0.5, xref="x", yref="y domain",
                text="SleepOnset",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)
            fig.add_annotation(
                x=multi_day_row['SleepOffset'],y=0.5, xref="x", yref="y domain",
                text="SleepOffset",showarrow=True,
                font=dict(family="Courier New, monospace",size=14,color="#34495E"),
                align="center", arrowhead=2,arrowsize=1,arrowwidth=1,arrowcolor="#636363",
                borderpad=3,bgcolor="#F2EFEE",)            
        except Exception as e:
               pass        
     

        fig.update_layout(xaxis=dict(dict(type='date' )),
            yaxis=dict(showticklabels=False),
            showlegend=False,
            plot_bgcolor='white')
        fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', showticklabels=True)    
        fig.update_xaxes(showgrid=False, zeroline=True,linewidth=1, linecolor='#898989',tickformat= '%H:%M') 
        fig.update_layout(xaxis_tick0 = range_start, xaxis_dtick=3600000,xaxis_range=[range_start,range_end],)
        return fig