from utilities.sleep_stagings import ThreeClassLabel, FourClassLabel

import matplotlib.pyplot as plt
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class MsltHypnogram:
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
        mapping = {0: 5, 1: 3, 2: 4, 10:None}
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
            return [['Wake', 'REM', 'NREM'], [2, 1, 0]]
        elif num_class_choice == len(FourClassLabel):
            return [['Wake', 'REM', 'Light', 'Deep'], [3, 2, 1, 0]]

    @classmethod
    def plotly_display(cls, labels, awakeings, times, heart_rates, num_class_choice, timezone, classifier_name=''):

        fig= make_subplots(specs=[[{"secondary_y": True}]])

        for idx, awakeing in enumerate(awakeings):
            new_awakeings = awakeing.loc[awakeing['value'] == 1]
            plot_awakenings = awakeing.copy()
            # set all values to zero
            plot_awakenings['value'].values[:] = 0
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
                            labels[idx].at[i] = labels[idx].iloc[prev_ind]
                            plot_awakenings.at[i, 'value'] = 1

                plot_awakenings_with_1 = plot_awakenings.loc[plot_awakenings['value'] == 1]
                awakeings_x = cls.time_conversion(plot_awakenings_with_1['time'].values, timezone)
                awakeings_y = [5.7] * len(plot_awakenings_with_1)    

                fig.add_trace(go.Scatter(x= awakeings_x, y=awakeings_y, mode='markers', name = 'Awakenings',
                        marker=dict(symbol = "line-ns", size=7, opacity=0.5,color='#E0821D',
                        line=dict( width=1, color= '#E0821D' )),)
                        )          
        
        def get_color(row):
            color_mapping = {3:'#2E3192', 4: '#779EDE', 5: '#2CC8C1'}
            return color_mapping[row]

        for index, label in enumerate(labels):  
               
            x = cls.time_conversion(times[index]['time'], timezone)
            y = cls.int_to_label(label.values, num_class_choice)
            new_lables = y
            label_color = list(map(get_color, new_lables))
            fig.add_trace(go.Scatter(y = y, x =x, mode='lines+markers', name = 'lables',
                line=dict(color='#5e54a9', width=0.3),connectgaps=True,marker=dict(symbol = "square", 
                size=6,opacity=0.6,color=label_color,line=dict(width=0)),)
                )

        for hr in heart_rates:
            fig.add_trace(go.Scatter( y = hr['value'].values, x =cls.time_conversion(hr['time'].values, timezone), mode="lines",
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

        fig.update_layout(xaxis=dict(dict(type='date' )),
            yaxis=dict(showticklabels=False),
            annotations=annotations,
            showlegend=False,
            plot_bgcolor='white')

        
        fig['layout']['yaxis2']['showticklabels']=False
        fig['layout']['yaxis2']['range']=[30,180]
        fig['layout']['height']=170
        fig['layout']['margin']=dict(t=40, b=20)

        fig.update_xaxes(showgrid=False, zeroline=True,linewidth=1, linecolor='#898989',tickformat= '%H:%M') 

        date = datetime.datetime.fromtimestamp(times[0]['time'].values[0])
        date_midnight =  datetime.datetime.combine(date, datetime.datetime.min.time())
        start_datetime = date_midnight + datetime.timedelta(hours=7)
        end_datetime = date_midnight + datetime.timedelta(hours=19)
        fig.update_layout(xaxis_range=[ start_datetime,end_datetime],xaxis_nticks=12)
        fig['layout']['height']=250 

        return fig