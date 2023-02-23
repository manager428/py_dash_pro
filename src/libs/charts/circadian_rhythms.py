import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime

class CircanianRhythms:
    def __init__(self, rhythm_multi_data, time_zone, height_of_subplot):
        self.time_zone = time_zone
        self.fig = None
        self.total_rows = None
        self.height_of_subplot = height_of_subplot if height_of_subplot else 150
        self.height_of_sleep = 7
        self.height_of_awakeing = 6
        self.range_of_hr = [30, 280]
        self.night_recordings = None

        self.rhythm_multi_data = rhythm_multi_data

    def three_class_int_to_label(self, labels):
        mapped = []
        mapping = {0: 5, 1: 3, 2: 4, 10:None}
        for label in labels:
            mapped.append(mapping[label])
        return mapped

    def time_conversion(self, time, time_zone=0):
        time_labels = []
        for t in time:
            time_labels.append(datetime.datetime.fromtimestamp(t + time_zone))
        return time_labels

    def arrange_sleep_time(self, df):
        df['TIMESTAMP'] = pd.to_numeric(df['TIMESTAMP'], errors='coerce').fillna(0.0).astype(np.float64)
        df['W/S'] = df['W/S'].astype(np.float64)
        df =  df[df['TIMESTAMP'] != 0]
        
        interp_time = np.arange(np.amin(df['TIMESTAMP'].values), np.amax(df['TIMESTAMP'].values), 30)
        interp_sleep = np.interp(interp_time, df['TIMESTAMP'].values, df['W/S'].values)
        sleep_color = ['#d6e2f5'] * len(interp_sleep)
        for i in range(len(interp_sleep)):
            if interp_sleep[i] == 0.0:
                sleep_color[i] = '#fbf8d9'
            if   pd.isna(interp_sleep[i]):
                sleep_color[i] = '#ffffff'    
        df_new = {}
        df_new['interp_time'] = interp_time
        df_new['interp_sleep'] = interp_sleep         
        df_new['sleep_color'] = sleep_color
        return df_new 

    def arrange_labels_colors(self, row):
        if row['labels'] ==0:
            return '#2CC8C1'
        if row['labels'] ==1:
            return '#2E3192'
        if row['labels'] ==2:
            return '#779EDE' 
        return 'black' 

    def get_time(self, row):
        return float(row['SK'].split('#')[2])
                 
    def clean_data(self):
        dates_with_data = 0
        new_night_recordings = {}
        for night_date, data in self.rhythm_multi_data.items():
            night_date = datetime.datetime.strptime(night_date, '%Y%m%d').replace(tzinfo=datetime.timezone.utc).date()
            night_date_midnight = datetime.datetime.combine(night_date, datetime.datetime.min.time())
            lookup_s_datetime = night_date_midnight - datetime.timedelta(hours=12)
            lookup_e_datetime = night_date_midnight + datetime.timedelta(hours=11, minutes=59)
            lookup_st = datetime.datetime.timestamp(lookup_s_datetime)
            lookup_et = datetime.datetime.timestamp(lookup_e_datetime)
            data['lookup_st'] = datetime.datetime.fromtimestamp(lookup_st ) 
            data['lookup_et'] = datetime.datetime.fromtimestamp(lookup_et )

            if not data['staging_df'].empty:
                data['staging_df']['time'] = data['staging_df'].apply(lambda row: self.get_time(row), axis=1)  
                new_awakeings = data['staging_df'].loc[data['staging_df']['awakening'] == 1]
                plot_awakenings = data['staging_df'].copy()
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
                                data['staging_df'].at[i, 'labels'] = data['staging_df'].iloc[prev_ind]['labels']
                                plot_awakenings.at[i, 'awakening'] = 1
                
                
                data['staging_df']['x'] = self.time_conversion(data['staging_df']['time'], data['time_zone'])
                data['staging_df']['y'] = self.three_class_int_to_label(data['staging_df']['labels'].values)
                data['staging_df']['color'] =data['staging_df'].apply(lambda row: self.arrange_labels_colors(row), axis=1)

                plot_awakenings_with_1 = plot_awakenings.loc[plot_awakenings['awakening'] == 1]
                awakeings_x = self.time_conversion(plot_awakenings_with_1['time'].values, data['time_zone'])
                awakeings_y = [1] * len(plot_awakenings_with_1)
                data['awakeing_df'] = {}
                data['awakeing_df']['awakeings_x'] = awakeings_x
                data['awakeing_df']['awakeings_y'] = awakeings_y
            
            if not data['sleep_df'].empty:
                data['sleep_df_new'] = self.arrange_sleep_time(data['sleep_df'])
            
            if data['hr_df'].empty is False or data['activity_df'].empty is False or data['staging_df'].empty is False or data['sleep_df'].empty is False:
                new_night_recordings[night_date] = data
                dates_with_data = dates_with_data + 1

        
        self.total_rows = dates_with_data 
        self.night_recordings = new_night_recordings 

    def create_traces(self):
        row = 1
        
        self.fig = make_subplots(rows= self.total_rows, cols= 1, vertical_spacing= 0.01 , row_heights= [1] * self.total_rows, specs=[[{"secondary_y": True}]] * self.total_rows) 
        for night_date, data in self.night_recordings.items():
            if data['hr_df'].empty is False:
                self.fig.add_trace(
                    go.Scatter(
                        y=data['hr_df']['HR'], x=self.time_conversion(data['hr_df']['TIMESTAMP'], data['time_zone']), 
                        mode='lines', line=dict(color='indianred', width=1), connectgaps=False, opacity=0.7, name = 'hr', showlegend=False
                    ), 
                    secondary_y= True,row= row, col= 1
                )
            if not data['activity_df'].empty:
                self.fig.add_trace(
                    go.Scatter(
                        y= data['activity_df']['ACTIVITY']/data['activity_df']['ACTIVITY'].max(), x= self.time_conversion(data['activity_df']['TIMESTAMP'], data['time_zone']), 
                        mode='lines', line=dict(color='lightseagreen', width=2), name='activity', showlegend=False
                    ), 
                    secondary_y= False, row= row, col= 1
                )
            if not data['staging_df'].empty:
                
                self.fig.add_trace(
                    go.Scatter(
                        y= data['staging_df']['y'], x= data['staging_df']['x'],  
                        mode='lines+markers', line=dict(color='#5e54a9', width=0.3), connectgaps=False, name='labels',
                        marker= dict(symbol= "square", size=5,opacity=0.6, color=data['staging_df']['color'], line=dict(width=0)), showlegend= False
                    ), 
                    secondary_y= False, row= row, col= 1
                )
                awakeing_df =  data['awakeing_df']
                if len(awakeing_df['awakeings_x']) > 0:
                    self.fig.add_trace(
                        go.Scatter(
                            y=[self.height_of_awakeing] * len(awakeing_df['awakeings_x']), x=awakeing_df['awakeings_x'],
                            mode='markers', name= 'Awakenings', marker=dict(symbol = "line-ns", size=6, opacity=0.5, color='#E0821D', line=dict( width=1, color= '#E0821D')), showlegend=False
                        ),
                        secondary_y=False, row=row, col=1
                    )
            if len(data['sleep_df_new']['interp_sleep']) > 0:
                self.fig.add_trace(
                    go.Bar(
                            y=[self.height_of_sleep] * len(data['sleep_df_new']['interp_sleep']), x=self.time_conversion(data['sleep_df_new']['interp_time'], data['time_zone']),
                            marker_color=data['sleep_df_new']['sleep_color'], marker_line_color=data['sleep_df_new']['sleep_color'], hoverinfo='none', showlegend=False
                        ),
                    secondary_y=False, row=row, col=1
                )
            row = row + 1

    def update_layout(self):
        annotations = []
        total_rows = self.total_rows
        i=1
        for night_date, data in self.night_recordings.items(): 
            self.fig['layout']['xaxis{}'.format(i)]['range']=[data['lookup_st'],data['lookup_et']]
            self.fig['layout']['xaxis{}'.format(i)]['showline']=True
            self.fig['layout']['xaxis{}'.format(i)]['linewidth']=1
            self.fig['layout']['xaxis{}'.format(i)]['linecolor']='gray'
            self.fig['layout']['xaxis{}'.format(i)]['showticklabels']=False
            self.fig['layout']['yaxis{}'.format((i*2))]['showticklabels']=False
            self.fig['layout']['yaxis{}'.format((i*2-1))]['showticklabels']=False
            self.fig['layout']['yaxis{}'.format((i*2))]['range']=self.range_of_hr

            if i == total_rows:
                self.fig['layout']['xaxis{}'.format(i)]['showticklabels']=True
                self.fig['layout']['xaxis{}'.format(i)]['tickformat']='%H:%M'
            
            annotations.append(dict(x=0, y=0,
                xref='x{} domain'.format(i if i !=1 else ''), 
                yref= 'y{} domain'.format(i*2), 
                xshift= -50,
                yshift = 20,  
                text = night_date.strftime('%m/%d'),  
                font_color='gray',
                font=dict(family='Arial',size=14),
                showarrow=False))
            
            annotations.append(dict(x=0, y=0,
                xref='x{} domain'.format(i if i !=1 else ''), 
                yref= 'y{} domain'.format(i*2), 
                xshift= -50,
                yshift = 40,         
                text='<b>{}</b>'.format(night_date.strftime('%a')),
                font_color='gray',
                font=dict(family='Arial',size=14),
                showarrow=False))    
                                 
            i=i+1
        
              
        self.fig.update_layout(margin=dict(t=40, b=20),bargap=0,plot_bgcolor="white")
        self.fig['layout']['height']=self.height_of_subplot*total_rows
        
        self.fig['layout']['annotations']=annotations    

    def plot(self):
        """Displays the plot"""
        self.clean_data()
        self.create_traces()
        self.update_layout()
        return self.fig 
                     