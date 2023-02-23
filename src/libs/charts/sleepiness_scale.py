import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime


class SleepinessScale:
    def __init__(self, data, height_of_subplot):
        self.fig = make_subplots(rows=len(data), cols=1, vertical_spacing=0.01, row_heights=[1] * len(data),
                                 specs=[[{}]] * len(data))
        self.data = data
        self.height_of_subplot = height_of_subplot if height_of_subplot else 250
        self.height_offset = 1
        self.range_of_hr = [30, 500]

    def three_class_int_to_label(self, labels):
        mapped = []
        mapping = {0: 5, 1: 3, 2: 4, 10: None}
        for label in labels:
            mapped.append(mapping[label])
        return mapped

    def time_conversion(self, time, time_zone=0):
        time_labels = []
        for t in time:
            time_labels.append(datetime.datetime.fromtimestamp(t + time_zone))
        return time_labels

    def arrange_crnn_time(self, dfs):
        results = []
        for df in dfs:
            df = df[df['time'] != 0]
            result = {}
            interp_time = np.arange(np.amin(df['time'].values), np.amax(df['time'].values), 30)
            interp_crnn = np.interp(interp_time, df['time'].values, df['value'].values)
            crnn_color = ['#d6e2f5'] * len(interp_crnn)
            for i in range(len(interp_crnn)):
                if interp_crnn[i] == 0.0:
                    crnn_color[i] = '#fbf8d9'
                if pd.isna(interp_crnn[i]):
                    crnn_color[i] = '#ffffff'

            result['interp_time'] = interp_time
            result['interp_crnn'] = interp_crnn
            result['crnn_color'] = crnn_color
            results.append(result)
        return results

    def arrange_lstm_time(self, dfs):
        results = []
        for df in dfs:
            df = df[df['time'] != 0]
            result = {}
            interp_time = np.arange(np.amin(df['time'].values), np.amax(df['time'].values), 30)
            interp_lstm = np.interp(interp_time, df['time'].values, df['value'].values)
            crnn_color = ['#d6e2f5'] * len(interp_lstm)
            for i in range(len(interp_lstm)):
                if interp_lstm[i] == 0.0:
                    crnn_color[i] = '#fbf8d9'
                if pd.isna(interp_lstm[i]):
                    crnn_color[i] = '#ffffff'

            result['interp_time'] = interp_time
            result['interp_lstm'] = interp_lstm
            results.append(result)
        return results

    def arrange_random_forest_time(self, dfs):
        results = []
        for df in dfs:
            df = df[df['time'] != 0]
            result = {}
            interp_time = np.arange(np.amin(df['time'].values), np.amax(df['time'].values), 500)
            interp_random_forest = np.interp(interp_time, df['time'].values, df['value'].values)
            random_forest_color = ['#d6e2f5'] * len(interp_random_forest)
            for i in range(len(interp_random_forest)):
                if interp_random_forest[i] == 0.0:
                    random_forest_color[i] = '#fbf8d9'
                if pd.isna(interp_random_forest[i]):
                    random_forest_color[i] = '#ffffff'

            result['interp_time'] = interp_time
            result['interp_random_forest'] = interp_random_forest
            results.append(result)
        return results

    def arrange_sleep_diary_time(self, sleep_diary_data, data):
        result = {}
        time_period = [data['lookup_st'].timestamp(), sleep_diary_data['start'].timestamp(), sleep_diary_data['start'].timestamp(),
                    sleep_diary_data['end'].timestamp(), sleep_diary_data['end'].timestamp(), data['lookup_et'].timestamp()]
        values = [0, 0, 1, 1, 0, 0]
        interp_time = np.arange(np.amin(time_period), np.amax(time_period), 3000)
        interp_sleep = np.interp(interp_time, time_period, values)
        sleep_color = ['#e1ded7'] * len(interp_sleep)
        for i in range(len(interp_sleep)):
            if interp_sleep[i] == 0.0:
                sleep_color[i] = '#faf6e9'
            if   pd.isna(interp_sleep[i]):
                sleep_color[i] = '#ffffff'    

        result['interp_time'] = interp_time
        result['interp_sleep'] = interp_sleep         
        result['sleep_color'] = sleep_color
        return result

    def arrange_labels_colors(self, row):

        if row['val'] == 0:
            return '#2CC8C1'
        if row['val'] == 1:
            return '#2E3192'
        if row['val'] == 2:
            return '#779EDE'
        return 'black'

    def clean_data(self):
        """Clean data"""

        for night_date, data in self.data.items():

            night_date_midnight = datetime.datetime.combine(night_date, datetime.datetime.min.time())
            lookup_s_datetime = night_date_midnight + datetime.timedelta(hours=12)
            lookup_e_datetime = night_date_midnight + datetime.timedelta(hours=35, minutes=59)

            lookup_st = datetime.datetime.timestamp(lookup_s_datetime)
            lookup_et = datetime.datetime.timestamp(lookup_e_datetime)

            night = data['recordings'][0]['night']
            sign = '+' if night[-6] == '--' else '-'
            try:
                time_zone = int(sign + str(int(night[-4:-2]) * 3600 + int(night[-2:]) * 60))
            except:
                time_zone = -25200
            data['time_zone'] = time_zone

            data['lookup_st'] = datetime.datetime.fromtimestamp(lookup_st)
            data['lookup_et'] = datetime.datetime.fromtimestamp(lookup_et)

            for recording in data['recordings']:
                if recording['hr'] is not None:
                    look_up = recording['hr']['time'].apply(lambda x: x + time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0:
                        if 'before_hr' in data:
                            data['before_hr'] = data['before_hr'].append(recording['hr'].iloc[0:start_index])
                        else:
                            data['before_hr'] = recording['hr'].iloc[0:start_index]

                    if end_index < len(recording['hr'].index):
                        if 'after_hr' in data:
                            data['after_hr'] = data['after_hr'].append(
                                recording['hr'][recording['hr'].index > end_index])
                        else:
                            data['after_hr'] = recording['hr'][recording['hr'].index > end_index]

                    if end_index > start_index:
                        if 'in_hr' in data:
                            data['in_hr'] = data['in_hr'].append(
                                {'time': data['in_hr']['time'].values[-1] + 2, 'value': None, }, ignore_index=True)
                            data['in_hr'] = data['in_hr'].append(recording['hr'].iloc[start_index + 1:end_index - 1],
                                                                 ignore_index=True)
                        else:
                            data['in_hr'] = recording['hr'].iloc[start_index + 1:end_index - 1]

                if recording['activity'] is not None:
                    look_up = recording['activity']['time'].apply(lambda x: x + time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0:
                        if 'before_activity' in data:
                            data['before_activity'] = data['before_activity'].append(
                                recording['activity'].iloc[0:start_index])
                        else:
                            data['before_activity'] = recording['activity'].iloc[0:start_index]

                    if end_index < len(recording['activity'].index):
                        if 'after_activity' in data:
                            data['after_activity'] = data['after_activity'].append(
                                recording['activity'][recording['activity'].index > end_index])
                        else:
                            data['after_activity'] = recording['activity'][recording['activity'].index > end_index]

                    if end_index > start_index:
                        if 'in_activity' in data:
                            data['in_activity'] = data['in_activity'].append(
                                {'time': data['in_activity']['time'].values[-1] + 2, 'count': None, },
                                ignore_index=True)
                            data['in_activity'] = data['in_activity'].append(
                                recording['activity'].iloc[start_index + 1:end_index - 1])
                        else:
                            data['in_activity'] = recording['activity'].iloc[start_index + 1:end_index - 1]

                if recording['crnn'] is not None:
                    look_up = recording['crnn']['time'].apply(lambda x: x + time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0:
                        if 'before_crnn' in data:
                            data['before_crnn'].append(recording['crnn'].iloc[0:start_index])
                        else:
                            data['before_crnn'] = []
                            data['before_crnn'].append(recording['crnn'].iloc[0:start_index])

                    if end_index < len(recording['crnn'].index):
                        if 'after_crnn' in data:
                            data['after_crnn'].append(recording['crnn'][recording['crnn'].index > end_index])
                        else:
                            data['after_crnn'] = []
                            data['after_crnn'].append(recording['crnn'][recording['crnn'].index > end_index])

                    if end_index > start_index:
                        if 'in_crnn' in data:
                            data['in_crnn'].append(recording['crnn'].iloc[start_index + 1:end_index - 1])
                        else:
                            data['in_crnn'] = []
                            data['in_crnn'].append(recording['crnn'].iloc[start_index + 1:end_index - 1])

                if recording['lstm'] is not None:
                    look_up = recording['lstm']['time'].apply(lambda x: x + time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0:
                        if 'before_lstm' in data:
                            data['before_lstm'].append(recording['lstm'].iloc[0:start_index])
                        else:
                            data['before_lstm'] = []
                            data['before_lstm'].append(recording['lstm'].iloc[0:start_index])

                    if end_index < len(recording['lstm'].index):
                        if 'after_lstm' in data:
                            data['after_lstm'].append(recording['lstm'][recording['lstm'].index > end_index])
                        else:
                            data['after_lstm'] = []
                            data['after_lstm'].append(recording['lstm'][recording['lstm'].index > end_index])

                    if end_index > start_index:
                        if 'in_lstm' in data:
                            data['in_lstm'].append(recording['lstm'].iloc[start_index + 1:end_index - 1])
                        else:
                            data['in_lstm'] = []
                            data['in_lstm'].append(recording['lstm'].iloc[start_index + 1:end_index - 1])

                if recording['random_forest'] is not None:
                    look_up = recording['random_forest']['time'].apply(lambda x: x + time_zone)
                    start_index = look_up.searchsorted(lookup_st)
                    end_index = look_up.searchsorted(lookup_et)
                    if start_index != 0:
                        if 'before_random_forest' in data:
                            data['before_random_forest'].append(recording['random_forest'].iloc[0:start_index])
                        else:
                            data['before_random_forest'] = []
                            data['before_random_forest'].append(recording['random_forest'].iloc[0:start_index])

                    if end_index < len(recording['random_forest'].index):
                        if 'after_random_forest' in data:
                            data['after_random_forest'].append(recording['random_forest'][recording['random_forest'].index > end_index])
                        else:
                            data['after_random_forest'] = []
                            data['after_random_forest'].append(recording['random_forest'][recording['random_forest'].index > end_index])

                    if end_index > start_index:
                        if 'in_random_forest' in data:
                            data['in_random_forest'].append(recording['random_forest'].iloc[start_index + 1:end_index - 1])
                        else:
                            data['in_random_forest'] = []
                            data['in_random_forest'].append(recording['random_forest'].iloc[start_index + 1:end_index - 1])

                if recording['sleep_diary'] is not None:
                    data['in_sleep_diary'] = recording['sleep_diary']
                    
                if recording['kss_data'] is not None:
                    
                    for i in range(len(recording['kss_data']['time'])):
                        look_up = datetime.datetime.timestamp(recording['kss_data']['time'][i])
                        if look_up < lookup_st:
                            if 'before_kss_data' in data:
                                if recording['kss_data']['time'][i] not in data['before_kss_data']['time']:
                                    data['before_kss_data']['time'].append(recording['kss_data']['time'][i])
                                    data['before_kss_data']['rate'].append(recording['kss_data']['rate'][i])
                            else:
                                data['before_kss_data'] = {
                                    'time': [],
                                    'rate': [],
                                }
                                if recording['kss_data']['time'][i] not in data['before_kss_data']['time']:
                                    data['before_kss_data']['time'].append(recording['kss_data']['time'][i])
                                    data['before_kss_data']['rate'].append(recording['kss_data']['rate'][i])
                        
                        elif look_up >= lookup_st and look_up < lookup_et:
                            if 'in_kss_data' in data:
                                if recording['kss_data']['time'][i] not in data['in_kss_data']['time']:
                                    data['in_kss_data']['time'].append(recording['kss_data']['time'][i])
                                    data['in_kss_data']['rate'].append(recording['kss_data']['rate'][i])
                            else:
                                data['in_kss_data'] = {
                                    'time': [],
                                    'rate': [],
                                }
                                if recording['kss_data']['time'][i] not in data['in_kss_data']['time']:
                                    data['in_kss_data']['time'].append(recording['kss_data']['time'][i])
                                    data['in_kss_data']['rate'].append(recording['kss_data']['rate'][i])
                        else:
                            if 'after_kss_data' in data:
                                if recording['kss_data']['time'][i] not in data['after_kss_data']['time']:
                                    data['after_kss_data']['time'].append(recording['kss_data']['time'][i])
                                    data['after_kss_data']['rate'].append(recording['kss_data']['rate'][i])
                            else:
                                data['after_kss_data'] = {
                                    'time': [],
                                    'rate': [],
                                }
                                if recording['kss_data']['time'][i] not in data['after_kss_data']['time']:
                                    data['after_kss_data']['time'].append(recording['kss_data']['time'][i])
                                    data['after_kss_data']['rate'].append(recording['kss_data']['rate'][i])

            del data['recordings']

        for night_date, data in self.data.items():
            if 'before_crnn' in data:
                data['before_crnn_data'] = self.arrange_crnn_time(data['before_crnn'])
            if 'after_crnn' in data:
                data['after_crnn_data'] = self.arrange_crnn_time(data['after_crnn'])
            if 'in_crnn' in data:
                data['in_crnn_data'] = self.arrange_crnn_time(data['in_crnn'])
                del data['in_crnn']

            if 'before_lstm' in data:
                data['before_lstm_data'] = self.arrange_lstm_time(data['before_lstm'])
            if 'after_lstm' in data:
                data['after_lstm_data'] = self.arrange_lstm_time(data['after_lstm'])
            if 'in_lstm' in data:
                data['in_lstm_data'] = self.arrange_lstm_time(data['in_lstm'])
                del data['in_lstm']

            if 'before_random_forest' in data:
                data['before_random_forest_data'] = self.arrange_random_forest_time(data['before_random_forest'])
            if 'after_random_forest' in data:
                data['after_random_forest_data'] = self.arrange_random_forest_time(data['after_random_forest'])
            if 'in_random_forest' in data:
                data['in_random_forest_data'] = self.arrange_random_forest_time(data['in_random_forest'])
                del data['in_random_forest']
            
            prev_date = night_date + datetime.timedelta(days=-1)
            next_date = night_date + datetime.timedelta(days=1)
            if prev_date in self.data and 'after_kss_data' in self.data[prev_date]:
                if 'in_kss_data' in data:
                    data['in_kss_data']['time'].extend(self.data[prev_date]['after_kss_data']['time'])
                    data['in_kss_data']['rate'].extend(self.data[prev_date]['after_kss_data']['rate'])
                else:
                    data['in_kss_data'] = {
                        'time': [],
                        'rate': [],
                    }
                    data['in_kss_data']['time'] = self.data[prev_date]['after_kss_data']['time']
                    data['in_kss_data']['rate'] = self.data[prev_date]['after_kss_data']['rate']
            if next_date in self.data and 'before_kss_data' in self.data[next_date]:
                if 'in_kss_data' in data:
                    data['in_kss_data']['time'].extend(self.data[next_date]['before_kss_data']['time'])
                    data['in_kss_data']['rate'].extend(self.data[next_date]['before_kss_data']['rate'])
                else:
                    data['in_kss_data'] = {
                        'time': [],
                        'rate': [],
                    }
                    data['in_kss_data']['time'] = self.data[next_date]['before_kss_data']['time']
                    data['in_kss_data']['rate'] = self.data[next_date]['before_kss_data']['rate']    
            
            if 'in_sleep_diary' in data:
                data['in_sleep_diary'] = self.arrange_sleep_diary_time(data['in_sleep_diary'], data)


    def create_traces(self):
        """Adds all the traces"""
        row = 1

        for night_date, data in self.data.items():
            prev_date = night_date + datetime.timedelta(days=-1)
            next_date = night_date + datetime.timedelta(days=1)
            if 'in_kss_data' in data:
                self.fig.add_trace(go.Scatter(y=np.array(data['in_kss_data']['rate']) + [self.height_offset] * len(data['in_kss_data']['rate']),
                                              x=data['in_kss_data']['time'],
                                              mode='lines+markers',
                                              line=dict(color='pink', width=2), name='Karolinska-Scale',
                                              customdata=data['in_kss_data']['rate'],
                                              hovertemplate="%{x} %{customdata}",
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)

            if 'in_sleep_diary' in data:
                self.fig.add_trace(go.Bar(y=[1] * len(data['in_sleep_diary']['interp_sleep']), 
                            x=self.time_conversion(data['in_sleep_diary']['interp_time']),
                            marker_color=data['in_sleep_diary']['sleep_color'], 
                            marker_line_color=data['in_sleep_diary']['sleep_color'], hoverinfo='none', name='Sleep-Dialy',
                            showlegend=False),
                        secondary_y=False, row=row, col=1) 

            if 'in_hr' in data:
                self.fig.add_trace(go.Scatter(y=data['in_hr']['value']/180,
                                              x=self.time_conversion(data['in_hr']['time'], data['time_zone']),
                                              mode='lines', line=dict(color='indianred', width=1), connectgaps=False,
                                              opacity=0.7, name='hr',
                                              customdata=data['in_hr']['value'],
                                              hovertemplate="%{x} %{customdata}",
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)

            if prev_date in self.data and 'after_hr' in self.data[prev_date]:
                self.fig.add_trace(go.Scatter(y=self.data[prev_date]['after_hr']['value']/180,
                                              x=self.time_conversion(self.data[prev_date]['after_hr']['time'], data['time_zone']),
                                              mode='lines', line=dict(color='indianred', width=1), connectgaps=False,
                                              opacity=0.7, name='hr',
                                              customdata=self.data[prev_date]['after_hr']['value'],
                                              hovertemplate="%{x} %{customdata}",
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)

            if next_date in self.data and 'before_hr' in self.data[next_date]:
                self.fig.add_trace(go.Scatter(y=self.data[next_date]['before_hr']['value']/180,
                                              x=self.time_conversion(self.data[next_date]['before_hr']['time'], data['time_zone']),
                                              mode='lines', line=dict(color='indianred', width=1), connectgaps=False,
                                              opacity=0.7, name='hr',
                                              customdata=self.data[next_date]['before_hr']['value'],
                                              hovertemplate="%{x} %{customdata}",
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)
            
            if 'in_activity' in data:
                self.fig.add_trace(go.Scatter(y=data['in_activity']['counts'] / data['in_activity']['counts'].max(),
                                              x=self.time_conversion(data['in_activity']['time'], data['time_zone']),
                                              mode='lines',
                                              line=dict(color='lightseagreen', width=2), name='activity',
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)

            if prev_date in self.data and 'after_activity' in self.data[prev_date]:
                self.fig.add_trace(go.Scatter(y=self.data[prev_date]['after_activity']['counts'] / self.data[prev_date]['after_activity']['counts'].max(),
                                              x=self.time_conversion(self.data[prev_date]['after_activity']['time'], data['time_zone']),
                                              mode='lines',
                                              line=dict(color='lightseagreen', width=2), name='activity',
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)
                                   
            if next_date in self.data and 'before_activity' in self.data[next_date]:
                self.fig.add_trace(go.Scatter(y=self.data[next_date]['before_activity']['counts'] / self.data[next_date]['before_activity']['counts'].max(),
                                              x=self.time_conversion(self.data[next_date]['before_activity']['time'], data['time_zone']),
                                              mode='lines',
                                              line=dict(color='lightseagreen', width=2), name='activity',
                                              showlegend=False),
                                   secondary_y=False, row=row, col=1)

            if 'in_crnn_data' in data:
                for crnn_data in data['in_crnn_data']:
                    self.fig.add_trace(go.Scatter(y=crnn_data['interp_crnn'] + [self.height_offset] * len(crnn_data['interp_crnn']),
                                                  x=self.time_conversion(crnn_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='blue', width=2), name='crnn',
                                                  customdata=crnn_data['interp_crnn'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if prev_date in self.data and 'after_crnn_data' in self.data[prev_date]:
                for crnn_data in self.data[prev_date]['after_crnn_data']:
                    self.fig.add_trace(go.Scatter(y=crnn_data['interp_crnn'] + [self.height_offset] * len(crnn_data['interp_crnn']),
                                                  x=self.time_conversion(crnn_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='blue', width=2), name='crnn',
                                                  customdata=crnn_data['interp_crnn'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if next_date in self.data and 'before_crnn_data' in self.data[next_date]:
                for crnn_data in self.data[next_date]['before_crnn_data']:
                    self.fig.add_trace(go.Scatter(y=crnn_data['interp_crnn'] + [self.height_offset] * len(crnn_data['interp_crnn']),
                                                  x=self.time_conversion(crnn_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='blue', width=2), name='crnn',
                                                  customdata=crnn_data['interp_crnn'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)
            if 'in_lstm_data' in data:
                for lstm_data in data['in_lstm_data']:
                    self.fig.add_trace(go.Scatter(y=lstm_data['interp_lstm'] + [self.height_offset] * len(lstm_data['interp_lstm']),
                                                  x=self.time_conversion(lstm_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='green', width=2), name='lstm',
                                                  customdata=lstm_data['interp_lstm'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if prev_date in self.data and 'after_lstm_data' in self.data[prev_date]:
                for lstm_data in self.data[prev_date]['after_lstm_data']:
                    self.fig.add_trace(go.Scatter(y=lstm_data['interp_lstm'] + [self.height_offset] * len(lstm_data['interp_lstm']),
                                                  x=self.time_conversion(lstm_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='green', width=2), name='lstm',
                                                  customdata=lstm_data['interp_lstm'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if next_date in self.data and 'before_lstm_data' in self.data[next_date]:
                for lstm_data in self.data[next_date]['before_lstm_data']:
                    self.fig.add_trace(go.Scatter(y=lstm_data['interp_lstm'] + [self.height_offset] * len(lstm_data['interp_lstm']),
                                                  x=self.time_conversion(lstm_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='green', width=2), name='lstm',
                                                  customdata=lstm_data['interp_lstm'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if 'in_random_forest_data' in data:
                for random_forest_data in data['in_random_forest_data']:
                    self.fig.add_trace(go.Scatter(y=random_forest_data['interp_random_forest'] + [self.height_offset] * len(random_forest_data['interp_random_forest']),
                                                  x=self.time_conversion(random_forest_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='red', width=2), name='random_forest',
                                                  customdata=random_forest_data['interp_random_forest'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if prev_date in self.data and 'after_random_forest_data' in self.data[prev_date]:
                for random_forest_data in self.data[prev_date]['after_random_forest_data']:
                    self.fig.add_trace(go.Scatter(y=random_forest_data['interp_random_forest'] + [self.height_offset] * len(random_forest_data['interp_random_forest']),
                                                  x=self.time_conversion(random_forest_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='red', width=2), name='random_forest',
                                                  customdata=random_forest_data['interp_random_forest'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            if next_date in self.data and 'before_random_forest_data' in self.data[next_date]:
                for random_forest_data in self.data[next_date]['before_random_forest_data']:
                    self.fig.add_trace(go.Scatter(y=random_forest_data['interp_random_forest']  + [self.height_offset] * len(random_forest_data['interp_random_forest']),
                                                  x=self.time_conversion(random_forest_data['interp_time'], data['time_zone']),
                                                  mode='lines',
                                                  line=dict(color='red', width=2), name='random_forest',
                                                  customdata=random_forest_data['interp_random_forest'],
                                                  hovertemplate="%{x} %{customdata}",
                                                  showlegend=False),
                                       secondary_y=False, row=row, col=1)

            row = row + 1

    def update_layout(self):
        annotations = []
        total_rows = len(self.data)
        i = 1
        for night_date, data in self.data.items():

            self.fig['layout']['xaxis{}'.format(i)]['range'] = [data['lookup_st'], data['lookup_et']]
            self.fig['layout']['xaxis{}'.format(i)]['showline'] = True
            self.fig['layout']['xaxis{}'.format(i)]['linewidth'] = 1
            self.fig['layout']['xaxis{}'.format(i)]['linecolor'] = 'gray'
            self.fig['layout']['xaxis{}'.format(i)]['showticklabels'] = False
            self.fig['layout']['yaxis{}'.format(i)]['showticklabels'] = False
            # self.fig['layout']['yaxis{}'.format((i * 2))]['showticklabels'] = False
            # self.fig['layout']['yaxis{}'.format((i * 2 - 1))]['showticklabels'] = False
            # self.fig['layout']['yaxis{}'.format((i * 2))]['range'] = self.range_of_hr

            if i == total_rows:
                self.fig['layout']['xaxis{}'.format(i)]['showticklabels'] = True
                self.fig['layout']['xaxis{}'.format(i)]['tickformat'] = '%H:%M'

            annotations.append(dict(x=0, y=0,
                                    xref='x{} domain'.format(i if i != 1 else ''),
                                    yref='y{} domain'.format(i if i !=1 else ''),
                                    xshift=-50,
                                    yshift=20,
                                    text=night_date.strftime('%m/%d'),
                                    font_color='gray',
                                    font=dict(family='Arial', size=14),
                                    showarrow=False))

            annotations.append(dict(x=0, y=0,
                                    xref='x{} domain'.format(i if i != 1 else ''),
                                    yref='y{} domain'.format(i if i !=1 else ''),
                                    xshift=-50,
                                    yshift=40,
                                    text='<b>{}</b>'.format(night_date.strftime('%a')),
                                    font_color='gray',
                                    font=dict(family='Arial', size=14),
                                    showarrow=False))

            i = i + 1

        self.fig.update_layout(margin=dict(t=40, b=20), bargap=0, plot_bgcolor="white")
        self.fig['layout']['height'] = self.height_of_subplot * total_rows

        self.fig['layout']['annotations'] = annotations

    def plot(self):
        """Displays the plot"""
        self.clean_data()
        self.create_traces()
        self.update_layout()
        return self.fig
