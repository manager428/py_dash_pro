from utilities.sleep_stagings import ThreeClassLabel, FourClassLabel

import matplotlib.pyplot as plt
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class Hypnogram:
    @staticmethod
    def time_for_display(epochs_time, time_zone):
        time_labels = []
        for t in epochs_time:
            d = datetime.datetime.fromtimestamp(t + time_zone)
            time_labels.append(d.strftime('%H:%M:%S'))
        return time_labels

    def time_conversion(epochs_time, time_zone):
        time_labels = []
        for t in epochs_time:
            time_labels.append(datetime.datetime.fromtimestamp(t + time_zone))
        return time_labels    

    @classmethod
    def int_to_label(cls, labels, num_class_choice):
        if num_class_choice == len(ThreeClassLabel):
            return cls.three_class_int_to_label(labels)
        elif num_class_choice == len(FourClassLabel):
            return cls.four_class_int_to_label(labels)

    @classmethod
    def disply(cls, labels, subject_id, num_class_choice, time_zone, time=None, classifier_name=''):
        x = cls.time_for_display(time, time_zone)
        y = cls.int_to_label(labels, num_class_choice)

        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_yticks([2, 1, 0])
        ax.set_yticklabels(['Wake', 'REM', 'NREM'])
        plt.title('Sleep hypnogram for subject {} with {} classifier'.format(subject_id, classifier_name))
        plt.show()

    @staticmethod
    def three_class_int_to_label(labels):
        mapped = []
        mapping = {0: 0, 1: 1, 2: 2}
        for label in labels:
            mapped.append(mapping[label])
        return mapped

    @staticmethod
    def four_class_int_to_label(labels):
        mapped = []
        mapping = {0: 3, 1: 1, 2: 0, 3: 2}
        for label in labels:
            mapped.append(mapping[label])
        return mapped

    @staticmethod
    def get_ytick_label(num_class_choice):
        if num_class_choice == len(ThreeClassLabel):
            return [['REM', 'NREM', 'Wake'], [2, 1, 0]]
        elif num_class_choice == len(FourClassLabel):
            return [['Wake', 'REM', 'Light', 'Deep'], [3, 2, 1, 0]]

    @classmethod
    def plotly_display(cls, df_staging, num_class_choice, timezone, heart_rate=None, classifier_name=''):
        
        def get_time(row):
            return float(row['SK'].split('#')[2])
        df_staging['time'] = df_staging.apply(lambda row: get_time(row), axis=1)

        new_awakeings = df_staging.loc[df_staging['awakening'] == 1]
        plot_awakenings = df_staging.copy()
        # set all values to zero
        plot_awakenings['awakening'].values[:] = 0
        if not new_awakeings.empty :
            new_awakeings_indexes = new_awakeings.index

            indices = []
            temp = [new_awakeings_indexes[0]]
            for i, ind in enumerate(new_awakeings_indexes[1:]):
                if ind == new_awakeings_indexes[i] + 1:
                    temp.append(ind)
                else:
                    indices.append(temp)
                    temp = [ind]
            indices.append(temp)

            for arr in indices:
                if len(arr) < 6:
                    prev_ind = arr[0] - 1
                    for i in arr:
                        df_staging.at[i, 'labels'] = df_staging.iloc[prev_ind]['labels']
                        plot_awakenings.at[i, 'awakening'] = 1
            
        x = cls.time_conversion(df_staging['time'], timezone)
        y = cls.int_to_label(df_staging['labels'].values, num_class_choice)

        range_start = x[0].replace(minute=0, second=0)
        range_end = x[-1]

        time_range = pd.date_range(range_start, range_end , freq='H')

        plot_awakenings_with_1 = plot_awakenings.loc[plot_awakenings['awakening'] == 1]
        awakeings_x = cls.time_conversion(plot_awakenings_with_1['time'].values, timezone)
        awakeings_y = [3] * len(plot_awakenings_with_1)
        
        def get_width(row):
            
            if row['new_lables'] ==0:
                return 6
            if row['new_lables'] ==1:
                return 6
            if row['new_lables'] ==2:
                return 6

        def get_color(row):
            
            if row['new_lables'] ==0:
                return '#2CC8C1'
            if row['new_lables'] ==1:
                return '#2E3192'
            if row['new_lables'] ==2:
                return '#779EDE'                
        
        df_staging['new_lables'] = y
        df_staging['x'] = x
        # labels['width'] = labels.apply(lambda row: get_width(row), axis=1)
        df_staging['color'] = df_staging.apply(lambda row: get_color(row), axis=1)
        if heart_rate is not None:
            fig= make_subplots(specs=[[{"secondary_y": True}]])
        else:    
            fig = go.Figure()

        fig.add_trace(go.Scatter(y = y, x =x, mode='lines+markers', name = 'lables',
                                 line=dict(color='#5e54a9', width=0.3),
                                 connectgaps=True,
                                 marker=dict(
                                    symbol = "square", 
                                    size=6,
                                    opacity=0.6,
                                    color=df_staging['color'],
                                    line=dict(width=0)
                                    ),
                                 ))


        fig.add_trace(go.Scatter(x= awakeings_x, y=awakeings_y, mode='markers', name = 'Awakenings',
                                 marker=dict(
                                    symbol = "line-ns", 
                                    size=7,
                                    opacity=0.5,
                                    color='#E0821D',
                                    line=dict(
                                        width=1,
                                        color= '#E0821D'
                                    )
                                ),
                                 ))                         
        if  heart_rate is not None :
            fig.add_trace(go.Scatter( y = heart_rate['value'].values, x =cls.time_conversion(heart_rate['time'].values, timezone), mode="lines",
                name="hr", marker_color='indianred', opacity=0.6), secondary_y=True)

        annotations = []
        for stage, ytick in zip(*cls.get_ytick_label(num_class_choice)):
            annotations.append(dict(xref='paper', x=0.0001, y=ytick,
                                    xanchor='right', yanchor='middle',
                                    text=stage,
                                    showarrow=False))

        annotations.append(dict(xref='paper', x=0.0001, y=3,
                                    xanchor='right', yanchor='middle',
                                    text=  'Awakenings',
                                    font=dict(color="#E0821D"),
                                    showarrow=False)) 
        
        if  heart_rate is  None :
            fig.add_shape(type="line",
                x0=x[0].replace(minute=0, second=0), y0=3, x1=x[-1], y1=3,
                line=dict(
                    color="#808080",
                    width=0.5,
                    dash="dot",
                )
            )
        if  heart_rate is  None :
            for time in time_range:
                fig.add_shape(type="line",
                x0=time, y0=-0.5, x1=time, y1=3.5,
                line=dict(
                    color="#808080",
                    width=0.5,
                    dash="dot",
                )
            )

        fig.update_layout(xaxis=dict(dict(type='date' )),
            yaxis=dict(showticklabels=False),
            annotations=annotations,
            showlegend=False,
            plot_bgcolor='white')

        if  heart_rate is not None :
            fig['layout']['yaxis2']['showticklabels']=False
            fig['layout']['yaxis2']['range']=[30,180]
            fig['layout']['height']=170
            fig['layout']['margin']=dict(t=40, b=20)

        fig.update_xaxes(showgrid=False, zeroline=True,linewidth=1, linecolor='#898989',tickformat= '%H:%M') 
        
        if  heart_rate is not None :
            if range_start.hour < 12 :
               date_midnight =  datetime.datetime.combine(range_start+datetime.timedelta(days=-1), datetime.datetime.min.time())
            else :
                date_midnight =  datetime.datetime.combine(range_start, datetime.datetime.min.time())   
            start_datetime = date_midnight + datetime.timedelta(hours=12)
            end_datetime = date_midnight + datetime.timedelta(hours=35, minutes=59)
            fig.update_layout(xaxis_range=[ start_datetime,end_datetime],xaxis_nticks=9)
            fig['layout']['height']=250

        else:
            fig.update_layout(xaxis_tick0 = range_start, xaxis_dtick=3600000)  

        return fig