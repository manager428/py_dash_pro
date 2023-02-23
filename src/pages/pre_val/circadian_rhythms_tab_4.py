from numpy.lib.utils import safe_eval
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime
from typing import Text, Union
import datetime
from pprint import pprint as pp
from dateutil.parser import parse


class MsltCircanianRhythms:
    def __init__(self, data , time_zone, height_of_subplot):
        self.time_zone = time_zone
        self.date_range = self.get_date_range(data)
        # self.fig = make_subplots(rows=len(self.date_range), cols=1, vertical_spacing=0.01 , row_heights=[1]*len(self.date_range) , specs=[[{"secondary_y": True}]]*len(self.date_range))
        self.fig = None
        self.total_rows = None
        self.data = data
        self.height_of_subplot = height_of_subplot if height_of_subplot else 150
        self.height_of_sleep = 7
        self.height_of_awakeing = 6
        self.range_of_hr = [30,280]
        self.night_recordings = None

    def three_class_int_to_label(self, labels):
        mapped = []
        mapping = {0: 5, 1: 3, 2: 4, 10:None}
        for label in labels:
            mapped.append(mapping[label])
        return mapped

    def time_conversion(self,time, time_zone=0):
        time_labels = []
        for t in time:
            time_labels.append(datetime.datetime.fromtimestamp(t+time_zone))
        return time_labels

    def arrange_sleep_time(self, dfs ):
        results = []
        for df in dfs :
            df =  df[df['time'] != 0]
            result = {}
            interp_time = np.arange(np.amin(df['time'].values), np.amax(df['time'].values), 30)
            interp_sleep = np.interp(interp_time, df['time'].values, df['sleep_prob'].values)
            sleep_color = ['#d6e2f5'] * len(interp_sleep)
            for i in range(len(interp_sleep)):
                if interp_sleep[i] == 0.0:
                    sleep_color[i] = '#fbf8d9'
                if   pd.isna(interp_sleep[i]):
                    sleep_color[i] = '#ffffff'    

            result['interp_time'] = interp_time
            result['interp_sleep'] = interp_sleep         
            result['sleep_color'] = sleep_color
            results.append(result)
        return results 

    def arrange_labels_colors(self, row):
            
            if row['val'] ==0:
                return '#2CC8C1'
            if row['val'] ==1:
                return '#2E3192'
            if row['val'] ==2:
                return '#779EDE' 
            return 'black' 

    def get_date_range(self, data):
        
        min_date = None
        max_date = None
        lookup =   data['activity']
        for time in lookup:
            local_min_date = datetime.datetime.fromtimestamp(time['time'].min()+self.time_zone).date()
            local_max_date = datetime.datetime.fromtimestamp(time['time'].max()+self.time_zone).date()
            if not min_date:
                min_date = local_min_date
            else :
                if  local_min_date  < min_date:
                    min_date = local_min_date

            if not max_date:
                max_date = local_max_date
            else :
                if  local_max_date  > max_date:
                    max_date = local_max_date

        return pd.date_range(start=min_date, end=max_date)                  

        
    def clean_data(self):
        """Clean data"""
        night_recordings = {}
    
        for date in self.date_range:
            night_date_midnight = datetime.datetime.combine(date, datetime.datetime.min.time())
            lookup_s_datetime = night_date_midnight + datetime.timedelta(hours=7)
            lookup_e_datetime = night_date_midnight + datetime.timedelta(hours=19)
            lookup_st = datetime.datetime.timestamp(lookup_s_datetime)
            lookup_et = datetime.datetime.timestamp(lookup_e_datetime)
            night_recordings[night_date_midnight] = {}
            data = night_recordings[night_date_midnight]
            data['lookup_st'] = datetime.datetime.fromtimestamp(lookup_st ) 
            data['lookup_et'] = datetime.datetime.fromtimestamp(lookup_et )
            time_zone = self.time_zone
            data['time_zone'] = self.time_zone

            if self.data['hr'] is not None :
                for hr in self.data['hr'] :
                    look_up = hr['time'].apply(lambda x: x+time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0 :
                        if  'before_hr' in data:
                            data['before_hr'].append(hr.iloc[0:start_index])
                        else:
                            data['before_hr'] = []
                            data['before_hr'].append(hr.iloc[0:start_index])  

                    if  end_index < len(hr.index):
                        if  'after_hr' in data:    
                            data['after_hr'].append(hr[hr.index > end_index])
                        else:
                            data['after_hr']=[]
                            data['after_hr'].append(hr[hr.index > end_index])

                    if end_index >  start_index :
                        if  'in_hr' in data:
                            data['in_hr'].append(hr.iloc[start_index+1:end_index-1])
                        else:
                            data['in_hr']=[]
                            data['in_hr'].append(hr.iloc[start_index+1:end_index-1])

            if self.data['activity'] is not None :
                for activity in self.data['activity'] :
                    look_up = activity['time'].apply(lambda x: x+time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0 :
                        if  'before_activity' in data:
                            data['before_activity'].append(activity.iloc[0:start_index])
                        else:
                            data['before_activity'] = []
                            data['before_activity'].append(activity.iloc[0:start_index])  

                    if  end_index < len(activity.index):
                        if  'after_activity' in data:    
                            data['after_activity'].append(activity[activity.index > end_index])
                        else:
                            data['after_activity']=[]
                            data['after_activity'].append(activity[activity.index > end_index])

                    if end_index >  start_index :
                        if  'in_activity' in data:
                            data['in_activity'].append(activity.iloc[start_index+1:end_index-1])
                        else:
                            data['in_activity']=[]
                            data['in_activity'].append(activity.iloc[start_index+1:end_index-1])                 

            if 'sleep' in self.data :
                for sleep in self.data['sleep'] :
                    look_up = sleep['time'].apply(lambda x: x+time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0 : 
                        if  'before_sleep' in data: 
                            data['before_sleep'].append(sleep.iloc[0:start_index]) 
                        else:
                            data['before_sleep'] = []
                            data['before_sleep'].append(sleep.iloc[0:start_index]) 

                    if  end_index < len(sleep.index):
                        if  'after_sleep' in data: 
                            data['after_sleep'].append(sleep[sleep.index > end_index]) 
                        else:
                            data['after_sleep'] = []
                            data['after_sleep'].append(sleep[sleep.index > end_index])
                        
                    if end_index >  start_index :
                        if  'in_sleep' in data: 
                            data['in_sleep'].append(sleep.iloc[start_index+1:end_index-1]) 
                        else:
                            data['in_sleep'] = []
                            data['in_sleep'].append(sleep.iloc[start_index+1:end_index-1])

            if self.data['labels'] is not None : 
                    for index, lables in enumerate(self.data['labels']):
                        new_lables = pd.DataFrame({'time': self.data['times'][index]['time'], 'val': lables.values, 'awakeing':False })

                        awakeings = self.data['awakeings'][index]
                        new_awakeings = awakeings.loc[awakeings['value'] == 1]
                        if not new_awakeings.empty :
                            
                            new_awakeings_indexes = new_awakeings.index
                            new_lables['awakeing'].loc[new_awakeings_indexes] = False

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
                                        new_lables.at[i, 'val'] = new_lables.iloc[prev_ind]['val']
                                        new_lables.at[i, 'awakeing'] = True


                        look_up = new_lables['time'].apply(lambda x: x+time_zone)
                        start_index = look_up.searchsorted(lookup_st)
                        end_index =   look_up.searchsorted(lookup_et)
                        new_lables.dropna()
                        
                        if start_index != 0 :  
                            if  'before_lables' in data:
                                data['before_lables'].append(new_lables.iloc[0:start_index])
                            else:
                                data['before_lables']= []
                                data['before_lables'].append(new_lables.iloc[0:start_index])

                        if end_index < len(new_lables.index) :  
                            if  'after_lables' in data:
                                data['after_lables'].append(new_lables[new_lables.index > end_index])
                        
                            else:
                                data['after_lables']= []
                                data['after_lables'].append(new_lables[new_lables.index > end_index])
                                        
                        
                        if end_index >  start_index :
                            if  'in_lables' in data:
                                data['in_lables'].append(new_lables.iloc[start_index+1:end_index-1])
                        
                            else:
                                data['in_lables'] = []
                                data['in_lables'].append(new_lables.iloc[start_index+1:end_index-1])                


        self.night_recordings = night_recordings


        

        for night_date, data in self.night_recordings.items():
            if 'before_sleep' in data:
                data['before_sleep_data'] = self.arrange_sleep_time(data['before_sleep'])
            if 'after_sleep' in data:
                data['after_sleep_data'] = self.arrange_sleep_time(data['after_sleep'])
            if 'in_sleep' in data: 
                data['in_sleep_data'] = self.arrange_sleep_time(data['in_sleep'])
                del data['in_sleep']
            if 'before_lables' in data:
                for lables in data['before_lables']:
                    lables['color'] = lables.apply(lambda row: self.arrange_labels_colors(row), axis=1)

            if 'after_lables' in data:
                for lables in data['after_lables']:
                    lables['color'] = lables.apply(lambda row: self.arrange_labels_colors(row), axis=1)        
            if 'in_lables' in data:
                for lables in data['in_lables']:
                    lables['color'] = lables.apply(lambda row: self.arrange_labels_colors(row), axis=1)   
               
                     
    
    def create_traces(self):
        """Adds all the traces"""
        row = 1

        dates_with_data = 0
        new_night_recordings = {}

        for night_date, data in self.night_recordings.items():
            if any(key in data for key in ['in_hr', 'in_sleep_data', 'in_activity','in_lables']):
                new_night_recordings[night_date] = data
                dates_with_data = dates_with_data+1

        self.total_rows = dates_with_data 
        self.night_recordings = new_night_recordings       

        self.fig = make_subplots(rows=dates_with_data, cols=1, vertical_spacing=0.01 , 
                        row_heights=[1]*dates_with_data, specs=[[{"secondary_y": True}]]*dates_with_data)        


        for night_date, data in self.night_recordings.items():
            prev_date = night_date+datetime.timedelta(days=-1)
            next_date = night_date+datetime.timedelta(days=1)

            if  'in_hr' in data:
                for hr in data['in_hr']:
                    self.fig.add_trace(go.Scatter(y=hr['value'], x=self.time_conversion(hr['time'], data['time_zone']), 
                            mode='lines', line=dict(color='indianred', width=1),connectgaps=False, opacity=0.7,name = 'hr',
                            showlegend=False), 
                        secondary_y=True,row=row, col=1)

            if  'in_sleep_data' in data:
                for sleep_data in data['in_sleep_data']:
                    self.fig.add_trace(go.Bar(y=[self.height_of_sleep] * len(sleep_data['interp_sleep']), 
                            x=self.time_conversion(sleep_data['interp_time'],data['time_zone']),
                            marker_color=sleep_data['sleep_color'], marker_line_color=sleep_data['sleep_color'], hoverinfo='none',
                            showlegend=False),
                        secondary_y=False, row=row, col=1) 

            if  'in_activity' in data:
                for activity in data['in_activity']:
                    self.fig.add_trace(go.Scatter(y=activity['counts']/activity['counts'].max(), 
                            x=self.time_conversion(activity['time'],  data['time_zone']),mode='lines', 
                            line=dict(color='lightseagreen', width=2),name='activity',showlegend=False), 
                        secondary_y=False, row=row, col=1)

            if  'in_lables' in data:
                for lables in data['in_lables']:
                    awakeing_df =  lables.loc[lables['awakeing'] == True]
                    self.fig.add_trace(go.Scatter(y=self.three_class_int_to_label(lables['val']), 
                            x=self.time_conversion(lables['time'], data['time_zone']),  mode='lines+markers', 
                            line=dict(color='#5e54a9', width=0.3),connectgaps=False, name='labels',
                            marker=dict(symbol = "square", size=5,opacity=0.6,color=lables['color'],line=dict(width=0)),
                            showlegend=False), 
                        secondary_y=False, row=row, col=1)
                    if not awakeing_df.empty:
                        self.fig.add_trace(go.Scatter(x=self.time_conversion(awakeing_df['time'], data['time_zone']),
                            y=[self.height_of_awakeing] * len(awakeing_df), mode='markers', name = 'Awakenings',
                            marker=dict( symbol = "line-ns", size=6,opacity=0.5,color='#E0821D',
                            line=dict( width=1, color= '#E0821D')),showlegend=False),
                        secondary_y=False, row=row, col=1)                                                            
                    
            row = row+1

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
                     