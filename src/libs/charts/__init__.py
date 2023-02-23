import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import collections
import boto3
from boto3.dynamodb.conditions import Key
from src import application
from src.libs.utils import download_csv_file
from .sleep_trend import SleepTrend
from .circadian_rhythms import CircanianRhythms
from .sleepiness_scale import SleepinessScale

dynamodb = boto3.resource('dynamodb')
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE'])


def time_conversion(epochs_time, time_zone):
        time_labels = []
        for t in epochs_time:
            time_labels.append(datetime.datetime.fromtimestamp(t + time_zone))
        return time_labels 

def time_for_display(epochs_time, timezone):
        time_labels = []
        for t in epochs_time:
            d = datetime.datetime.fromtimestamp(t + timezone)
            time_labels.append(d.strftime('%H:%M:%S'))
        return time_labels

def generate_chart(stages_df):
        fig = go.Figure(data=[go.Pie(labels=stages_df['stage'], values=stages_df['time'], hole=.7)])
        return fig

def generate_hr_graph(hr, activity, timezone):
        fig = make_subplots(rows=3, cols=1)
        fig.append_trace(go.Scatter(y=hr[:, 1], x=time_for_display(hr[:, 0], timezone), mode='lines'), 1, 1)
        fig.append_trace(go.Scatter(y=abs(np.diff(hr[:, 1])), mode='lines'), 2, 1)
        fig.append_trace(go.Scatter(y=activity[:, 1], mode='lines'), 3, 1)

        layout = go.Layout(
            xaxis=dict(side='top'),
            xaxis2=dict(side='top', tickfont=dict(color='rgba(0,0,0,0)')),
            yaxis=dict(title='HR'),
            yaxis2=dict(title='HRV'),
            yaxis3=dict(title='Activity Count'),
            showlegend=False
        )
        fig['layout'].update(layout)
        return fig 

def generate_hr_chart(hr, timezone):
    
    x = time_conversion(hr["TIMESTAMP"], timezone)
    y= hr["HR"]

    range_start = x[0].replace(minute=0, second=0)
    range_end = x[-1]

    time_range = pd.date_range(range_start, range_end , freq='H')

    fig = go.Figure(data=[go.Scatter(y=y, x=x, line = dict(color='#F17E5D', width=1))])

    for time in time_range.tolist()[1:]:
        fig.add_shape(type="line",
        x0=time, y0=0, x1=time, y1=max(y),
        line=dict(
            color="#808080",
            width=0.5,
            dash="dot",
        )
        )
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black',tickformat= '%H:%M')
    fig.update_yaxes(showgrid=False,showline=True, linewidth=1, linecolor='black',showticklabels=True)
    fig.update_layout(
    plot_bgcolor="white",
    xaxis=dict(dict(type='date'))
    )
    fig.update_layout(xaxis_tick0 = range_start, xaxis_dtick=3600000,
          xaxis_range=[range_start,range_end],yaxis_range = [min(y)-5, max(y)+5])
    return fig

def generate_hrv_chart(hr, timezone):
    hr['hrv'] = hr['HR'].rolling(window=100).std()
    hr.fillna(hr['HR'].mean())

    x = time_conversion(hr['TIMESTAMP'], timezone)
    y=hr['hrv']

    range_start = x[0].replace(minute=0, second=0)
    range_end = x[-1]

    time_range = pd.date_range(range_start, range_end , freq='H') 


    fig = go.Figure(data=[go.Scatter(y=y, x=x, line = dict(color='#EB9982', width=1))])
    for time in time_range.tolist()[1:]:
        fig.add_shape(type="line",
        x0=time, y0=0, x1=time, y1=np.nanmax(y.values),
        line=dict(
            color="#808080",
            width=0.5,
            dash="dot",
        )
        )
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black',tickformat= '%H:%M')
    fig.update_yaxes(showgrid=False,showline=True, linewidth=1, linecolor='black',showticklabels=True)
    fig.update_layout(
    plot_bgcolor="white",
    xaxis=dict(dict(type='date'))
    )
    fig.update_layout(xaxis_tick0 = range_start, xaxis_dtick=3600000,
          xaxis_range=[range_start,range_end],yaxis_range = [min(y)-3, max(y)+3])
    return fig

def generate_activity_chart(activity, timezone):

    x = time_conversion(activity['TIMESTAMP'], timezone)
    y = activity['ACTIVITY']

    range_start = x[0].replace(minute=0, second=0)
    range_end = x[-1]
    time_range = pd.date_range(range_start, range_end , freq='H')

    fig = go.Figure(data=[go.Scatter(y=y,x=x, line = dict(color='#00A99D', width=1))])

    for time in time_range.tolist()[1:]:
        fig.add_shape(type="line",
        x0=time, y0=0, x1=time, y1=max(y),
        line=dict(
            color="#808080",
            width=0.5,
            dash="dot",
        )
        )

    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black',tickformat= '%H:%M')
    fig.update_yaxes(showgrid=False,showline=True, linewidth=1, linecolor='black',showticklabels=True)
    fig.update_layout(
    plot_bgcolor="white",
    xaxis=dict(dict(type='date'))
    )
    fig.update_layout(xaxis_tick0 = range_start, xaxis_dtick=3600000,
          xaxis_range=[range_start,range_end])
    return fig

def generate_awakeing_chart(aweking, time_zone):
    x = time_conversion(aweking['time'].values, time_zone)
    y = aweking['value'].values
    fig= go.Figure()
    fig.add_trace(go.Bar(x=x, y=y, name="aweking",marker_color='rgb(244, 125, 61)',
                marker_line_color='rgb(244, 155, 61)'))
    fig.update_layout(
    plot_bgcolor="white",
    xaxis=dict(dict(type='date'))
    )
    return fig

def generate_multi_night_tst_chart(data):
    x = [ parse(item['DateTime']).replace(tzinfo=None).date() for item in data]
    y = [ round(item['TST']/3600, 1)  for item in data] 
    y_rem = [ round(item['REM Time']/3600, 1)  for item in data]
    y_nrem = [ round(item['NREM Time']/3600, 1)  for item in data]
    y_wake = [ round(item['Wake Time']/3600, 1)  for item in data]
    fig= go.Figure()
    day_width_in_msec = (1000*3600*24)/2
    start_range = x[0] + relativedelta(days=-3)
    end_range = x[-1] + relativedelta(days=+3)
    fig.add_trace(go.Bar(x= x, y=y_nrem, width=day_width_in_msec, marker_color='#1B1464',
                text=y_nrem, name='NREM', textposition='outside'))
    fig.add_trace(go.Bar(x= x, y=y_rem, width=day_width_in_msec, marker_color='#779EDE',
                text=y_rem, name='REM', textposition='outside',))            
    fig.add_trace(go.Bar(x= x, y=y_wake, width=day_width_in_msec, marker_color='#2CC8C1',
                text=y_wake, name='WAKE', textposition='outside',))            
    fig.add_trace(go.Bar(x= x, y=y, width=day_width_in_msec, marker_color='#87DDF5',
                text=y, name='Sleep latency', textposition='outside',))
    
                                      
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(uniformtext_minsize=20)
                              
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='lightgray')
    fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='white')           
    fig.update_layout(
    plot_bgcolor="white",
    barmode='stack',
    title= dict(text="Total Sleep Time", font=dict(color = '#000000',family='Roboto',size=14)),
    xaxis=dict(dict(type='date')),
    xaxis_range=[start_range,end_range],
    yaxis_ticksuffix = 'h'
    )
    return fig

def generate_multi_night_tib_tst_chart(data):
    
    x = [ parse(item['SleepOffset']).replace(tzinfo=None).date() for item in data]
    tst_y = [ int(item['TST']/60) for item in data] 
    tib_y = [  int ((parse(item['OutOfBedTime']) - parse(item['BedTime'])).seconds/60)      for item in data]

    fig= go.Figure()
    day_width_in_msec = (1000*3600*24)/3
    start_range = x[0] + relativedelta(days=-3)
    end_range = x[-1] + relativedelta(days=+3)
    fig.add_trace(go.Bar(x= x, y=tib_y, width = day_width_in_msec, marker_color='gray',
                text=tib_y, name='Time in Bed', textposition='outside'))
    fig.add_trace(go.Bar(x= x, y=tst_y,width = day_width_in_msec, marker_color='lightgray',
                text=tst_y, name='Total Sleep Time', textposition='outside',))            

    fig.update_layout(uniformtext_minsize=20)
                              
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', 
            gridcolor='lightgray', tickvals = x, tickformat = '%d %b')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='white')           
    fig.update_layout(
    plot_bgcolor="white",
    barmode='group', bargap=0.30,bargroupgap=0.6,
    title= dict(text="  <b>Time in Bed (TIB) and Total Sleep Time (TST)</b> ", font=dict(color = '#424149',family='Roboto',size=16)),
    xaxis=dict(dict(type='date')),
    xaxis_range=[start_range,end_range],
    yaxis_ticksuffix = 'm'
    )
    return fig                 


def generate_multi_night_sleep_efficiency_chart(data):
    
    x = [ parse(item['SleepOffset']).replace(tzinfo=None).date() for item in data]
    y = [ round (float(item['Efficiency'].split("%")[0]) , 1)  for item in data]
    waso = [  round(item['WASO']/60, 1)   for item in data]
    sl = [ item['Sleep Latency']  for item in data]
    start_range = x[0] + relativedelta(days=-3)
    end_range = x[-1] + relativedelta(days=+3)
    day_width_in_msec = (1000*3600*24)/2
    fig= make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x= x, y=waso, width=day_width_in_msec, marker_color='#008080',
                text=waso, name='WASO',  textposition='inside', insidetextanchor='middle'),secondary_y=False)
    fig.add_trace(go.Bar(x= x, y=sl, width=day_width_in_msec, marker_color='#779EDE',
                text=sl, name='SL', textposition='inside', insidetextanchor='middle' ),secondary_y=False)
    
    
    fig.add_trace(go.Scatter( x=x,y=y,mode="lines+text+markers",
        name="Sleep Efficiency",text=y,
        textposition="bottom center",
        marker_color='#677A15'), secondary_y=True)
    fig.update_traces(texttemplate="%{y}")
    fig.update_layout(uniformtext_minsize=24)
                          
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', 
        gridcolor='lightgray', tickvals = x, tickformat = '%d %b')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='white',)           
    fig.update_layout(
    plot_bgcolor="white",
    title= dict(text="  <b>Sleep Efficiency</b> ", font=dict(color = '#424149',family='Roboto',size=16)),
    xaxis=dict(dict(type='date')),
    barmode='relative',
    xaxis_range=[start_range,end_range],
    yaxis_ticksuffix = 'm',
    yaxis2_range=[10,100],
    yaxis_range=[0,max(waso)+max(sl)+ 20],
    yaxis2_ticksuffix = '%'
    )
   
    return fig             

def generate_multi_night_rem_nrem_sleep_chart(data):
    x = [ parse(item['SleepOffset']).replace(tzinfo=None).date()  for item in data]
    rem_y = [ round(item['REM Time']/3600, 1)  for item in data] 
    nrem_y = [ round(item['NREM Time']/3600, 1)  for item in data] 
    tst_y = [   round(item['TST']/3600, 1)  for item in data]

    day_width_in_msec = (1000*3600*24)/2
    start_range = x[0] + relativedelta(days=-3)
    end_range = x[-1] + relativedelta(days=+3)

    fig= go.Figure()
    fig.add_trace(go.Bar(x= x, y=nrem_y, name='NREM', width=day_width_in_msec , marker_color='#2E3192',
                text=nrem_y, textposition='inside', insidetextanchor='middle'))
    fig.add_trace(go.Bar(x= x, y=rem_y,name='REM',width=day_width_in_msec, marker_color='#779EDE',
                text=rem_y, textposition='inside', insidetextanchor='middle'))

    annotations = []
    for tst in  dict(zip(x, tst_y)).items():
        annotations.append(dict(x=tst[0], y=tst[1]+0.3,xref='x',yref= 'y', 
                    text = tst[1],showarrow=False))           
                                                                                 

    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', 
                    gridcolor='lightgray', tickvals = x, tickformat = '%d %b')
    fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='white')           
    fig.update_layout(
    plot_bgcolor="white",
    annotations= annotations,
    barmode='stack',
    title= dict(text="  <b>Total, REM and NREM Sleep</b> ", font=dict(color = '#424149',family='Roboto',size=16)),
    xaxis=dict(dict(type='date')),
    xaxis_range=[start_range,end_range],
    yaxis_ticksuffix = 'h',
    )
    return fig 

def generate_multi_night_awekeing_chart(data):
    x = [ parse(item['SleepOffset']).replace(tzinfo=None).date() for item in data]
    awakeings = [ item['Awakenings'] for item in data] 
    fig= go.Figure()
    day_width_in_msec = 1000*3600*24/2
    start_range = x[0] + relativedelta(days=-3)
    end_range = x[-1] + relativedelta(days=+3)
    fig.add_trace(go.Bar(x= x, y=awakeings,name='Awakeings', width=day_width_in_msec, marker_color='#E0821D',
                text=awakeings, textposition='outside',marker_line_color='#E0821D'))
    fig.update_xaxes(showgrid=False,showline=True, linewidth=1, linecolor='black', 
            gridcolor='lightgray', tickvals = x, tickformat = '%d %b')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='white')           
    fig.update_layout(
    plot_bgcolor="white",
    title= dict(text="  <b>Awakenings</b> ", font=dict(color = '#424149',family='Roboto',size=16)),
    xaxis=dict(dict(type='date')),
    xaxis_range=[start_range,end_range],
    )
    return fig 

def generate_multi_night_sl_reml_chart(data):
    x = [ parse(item['DateTime']).replace(tzinfo=None) for item in data]
    sleep_l= [ item['Sleep Latency']  for item in data]
    rem_l= [ round(item['REM Latency']/60, 1)    for item in data]
    mean_sleep_l = np.mean(sleep_l)
    mean_rem_l= np.mean(rem_l)
    fig= go.Figure()
    fig.add_trace(go.Line(x= x, y=sleep_l,name='Sleep Latency', marker_color='rgb(244, 225, 61)',
                text=sleep_l, marker_line_color='rgb(244, 155, 61)'))
    fig.add_trace(go.Line(x= x, y=rem_l,name='REM Latency', marker_color='rgb(24, 225, 20)',
                text=rem_l, marker_line_color='rgb(244, 155, 61)'))
    fig.add_shape(
        go.layout.Shape(type="line",x0=x[0],y0=mean_sleep_l,x1=x[-1],y1=mean_sleep_l,
                line=dict(color="rgb(244, 225, 61)",width=1,dash="dash",),
    ))
    fig.add_shape(
        go.layout.Shape(type="line",x0=x[0],y0=mean_rem_l,x1=x[-1],y1=mean_rem_l,
                line=dict(color="rgb(24, 225, 20)",width=1,dash="dash",),
    ))            
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black', gridcolor='lightgray')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='white')           
    fig.update_layout(
    plot_bgcolor="white",
    yaxis_title="minute",
    title="Sleep , REM  Latency ",
    xaxis=dict(dict(type='date')),
    )
    return fig 

def generate_sleep_trends_chart(data):

    sleepDf =  pd.DataFrame.from_dict(data) 
    sleep_trend = SleepTrend(sleepDf)
    sleep_fig = sleep_trend.plot()
    return sleep_fig 

def dateparse (time_in_secs):    
    return datetime.datetime.fromtimestamp(float(time_in_secs))

def generate_circadian_rhythms(night_folders, height_of_subplot=None):

    all_labels = []
    all_times = []
    all_awakeings = []
    all_hr = []
    all_activity = []
    all_sleep=[]
    ngiht_recordings = {}

    night_folder_string = night_folders[0]['night']
    # convert timezone from 5 last characters of night name to seconds. '-0800' --> -28800 seconds
    time_zone = int(night_folder_string[-5] + str(int(night_folder_string[-4:-2]) * 3600 + int(night_folder_string[-2:]) * 60))

    for nights in night_folders :
        
        try:
            path_to_s3_processed = nights['path']+ '/' +nights['night']

            sleep = download_csv_file(path_to_s3_processed + '/sleep_wake.csv')
            if sleep is not None :
               all_sleep.append(sleep) 
            activity = download_csv_file(path_to_s3_processed + '/activity.csv')
            if activity is not None :
               all_activity.append(activity) 
            hr = download_csv_file(path_to_s3_processed + '/heartrate.csv') 
            if hr is not None :
               all_hr.append(hr) 

            

            next_label = True
            label_no = 0
            while  next_label:
                file_name = '/stage_prediction.csv' if label_no == 0 else '/stage_prediction_{}.csv'.format(label_no)
                labels = download_csv_file(path_to_s3_processed + file_name)
                
                if  labels is not None :    
                    all_labels.append(labels['labels'])
                    label_no+=1
                else:
                    next_label = False  

            next_time = True
            time_no = 0
            while  next_time:     
                file_name = '/epoch_time.csv' if time_no == 0 else '/epoch_time_{}.csv'.format(time_no)
                times = download_csv_file(path_to_s3_processed + file_name)
                if times is not None :    
                    all_times.append(times)
                    time_no+=1
                else:
                    next_time = False

            next_awakeing = True
            awakeing_no = 0
            while  next_awakeing:     
                file_name = '/awakenings.csv' if awakeing_no == 0 else '/awakenings_{}.csv'.format(awakeing_no)
                awakeings = download_csv_file(path_to_s3_processed + file_name)
                if awakeings is not None :    
                    all_awakeings.append(awakeings)
                    awakeing_no+=1
                else:
                    next_awakeing = False                


        except Exception as e:       
            print ("err in charts.py",e) 
        
        ngiht_recordings['sleep'] = all_sleep
        ngiht_recordings['activity'] = all_activity
        ngiht_recordings['hr'] = all_hr
        ngiht_recordings['labels'] = all_labels
        ngiht_recordings['awakeings'] = all_awakeings
        ngiht_recordings['times'] = all_times

    cr = CircanianRhythms(ngiht_recordings, time_zone, height_of_subplot)
    return cr.plot()


def get_sleep_diary(selected_patient, night_date):
    try:
        qa_response = db_table.query(
            KeyConditionExpression=Key('PK').eq("USER#{}".format(selected_patient)) &
                                Key('SK').eq("#SLEEP#%s" % night_date.strftime('%Y%m%d'))
        )
        sleep_diary_data = qa_response['Items'][0]
        start = sleep_diary_data['start']
        sign = '+' if start[-6] == '--' else '-'
        try:
            time_zone = int(sign + str(int(start[-4:-2]) * 3600 + int(start[-2:]) * 60))
        except:
            time_zone = -25200
        start_time = datetime.datetime.strptime(sleep_diary_data['start'], '%H:%M:%S%z').time()
        start_time = datetime.datetime.combine(night_date, start_time)
        start_time = start_time + datetime.timedelta(minutes=int(sleep_diary_data['latencyduration']))
        end_time = datetime.datetime.strptime(sleep_diary_data['end'], '%H:%M:%S%z').time()
        next_date = night_date + datetime.timedelta(days=1)
        end_time = datetime.datetime.combine(next_date, end_time)
        # start_time = datetime.datetime.fromtimestamp(start_time.timestamp() + time_zone)
        # end_time = datetime.datetime.fromtimestamp(end_time.timestamp() + time_zone)
        return {'start': start_time, 'end': end_time}
    except Exception as e:
        print("err in get_sleep_diary in charts.py", e)
        return None

def get_kss_data(selected_patient, night_date):
    
    qa_response = db_table.query(
        KeyConditionExpression=Key('PK').eq("USER#{}".format(selected_patient)) &
                               Key('SK').begins_with("#SLEEP#%s#kss#" % night_date.strftime('%Y%m%d'))
    )
    kss_list = qa_response['Items']
    kss_data = {
        'time': [],
        'rate': [],
    }
    kss_list = sorted(kss_list, key=lambda x: x['start'], reverse=False)
    for kss in kss_list:
        start_time = datetime.datetime.strptime(kss['start'], '%Y-%m-%dT%H:%M:%S%z').time()
        start_time = datetime.datetime.combine(night_date, start_time)
        
        kss_data['time'].append(start_time)
        kss_data['rate'].append(int(kss['R'])/10)
    return kss_data


def generate_sleepiness_scale(night_folders, height_of_subplot, selected_patient):
    sleepiness_scales = {}
    for nights in night_folders:

        try:
            night_date = parse(nights['night']).date()
        except Exception as e:
            epoch = download_csv_file(nights['path'] + '/' + nights['night'] + '/epoch_time.csv')
            night_date = datetime.datetime.fromtimestamp(epoch.iloc[0].values[0]).date()

        try:
            path_to_s3_processed = nights['path'] + '/' + nights['night']

            all_times = []
            all_awakeings = []

            crnn = download_csv_file(path_to_s3_processed + '/crnn_sleepiness.csv')
            lstm = download_csv_file(path_to_s3_processed + '/lstm_sleepiness.csv')
            random_forest = download_csv_file(path_to_s3_processed + '/random_forest_sleepiness.csv')
            activity = download_csv_file(path_to_s3_processed + '/activity.csv')
            hr = download_csv_file(path_to_s3_processed + '/heartrate.csv')
            sleep_diary = get_sleep_diary(selected_patient, night_date)
            kss_data = get_kss_data(selected_patient, night_date)

            next_time = True
            time_no = 0
            while next_time:
                file_name = '/epoch_time.csv' if time_no == 0 else '/epoch_time_{}.csv'.format(time_no)
                times = download_csv_file(path_to_s3_processed + file_name)
                if times is not None:
                    all_times.append(times)
                    time_no += 1
                else:
                    next_time = False

            if night_date in sleepiness_scales:

                sleepiness_scales[night_date]['recordings'].append({'night': nights['night'], 'crnn': crnn, 'hr': hr,
                                                                   'lstm': lstm, 'random_forest': random_forest,
                                                                   'times': all_times, 'activity': activity,
                                                                    'sleep_diary': sleep_diary, 'kss_data': kss_data})
            else:
                sleepiness_scales[night_date] = {'recordings': []}
                sleepiness_scales[night_date]['recordings'].append({'night': nights['night'], 'crnn': crnn, 'hr': hr,
                                                                   'lstm': lstm, 'random_forest': random_forest,
                                                                   'times': all_times, 'activity': activity,
                                                                    'sleep_diary': sleep_diary, 'kss_data': kss_data})
        except Exception as e:
            print("err in charts.py", e)
    cr = SleepinessScale(sleepiness_scales, height_of_subplot)
    return cr.plot()


def generate_hear_rate_chart(profile_json_df, start_date, end_date):
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="white",
        title= dict(text="  <b>Resting Heart Rate (RHR)</b> ", font=dict(color = '#424149',family='Roboto',size=16)),
    )
    hr_data = {}

    try:
        for index, row in profile_json_df.iterrows():
            if row['recording']:
                for recording in row['recording']:
                    recording_date = parse(recording).date()
                    if start_date <= recording_date <= end_date and  recording_date not in hr_data:
                        hr_data[recording_date] = row['rhr']
    except:
        pass



    if hr_data: 
        hr_data =  collections.OrderedDict(sorted(hr_data.items()))
        x = list(hr_data.keys())
        y =list( hr_data.values())
        start_range = x[0] + relativedelta(days=-3)
        end_range = x[-1] + relativedelta(days=+3)
        fig.add_trace(go.Scatter(
            x=x,y=y,
            mode="lines+text+markers",
            name="Hear rate average",
            text=y,
            textposition="bottom center",
            marker_color='#F17E5D'
        ))
        fig.update_traces(texttemplate='%{text:.2s}', textposition='top right')
        fig.update_layout(uniformtext_minsize=24)
                            
        fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='lightgray')
        fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='white')           
        fig.update_layout(
        xaxis=dict(dict(type='date')),
        xaxis_range=[start_range,end_range],
        yaxis_range=[50,100],
        )
    else:
        fig.update_xaxes(visible = False)
        fig.update_yaxes(visible = False)
        fig.add_annotation(xref='paper', yref='paper',
            text="Data Not Available",
            font=dict(size=24,color="gray"),
            showarrow=False,)

    return fig


def generate_narcolepsy_naps_chart(data):
    filtered_data = []
    for item in data:
        bedtime = parse(item['BedTime'])
        tst = int(item['TST'])
        if bedtime.hour >= 9 and bedtime.hour < 18 and tst < 4*3600:
            filtered_data.append(item)

    if len(filtered_data) > 0:
        x = [parse(item['BedTime']).replace(tzinfo=None) for item in filtered_data]
        tst_y = [int(item['TST']/60) for item in filtered_data]
        # tib_y = [int(item['TIB']/60) for item in filtered_data]

        fig = go.Figure()
        day_width_in_msec = (1000 * 3600 * 24) / 3
        start_range = x[0] + relativedelta(days=-3)
        end_range = x[-1] + relativedelta(days=+3)
        # fig.add_trace(go.Bar(x=x, y=tib_y, width=day_width_in_msec, marker_color='gray',
        #                      text=tib_y, name='Time in Bed', textposition='outside'))
        fig.add_trace(go.Bar(x=x, y=tst_y, width=day_width_in_msec, marker_color='lightgray',
                             text=tst_y, name='Naps', textposition='outside'))

        fig.update_layout(uniformtext_minsize=20)

        fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black',
                         gridcolor='lightgray', tickvals=x, tickformat='%d %b - %H:%M')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='white')
        fig.update_layout(
            plot_bgcolor="white",
            barmode='group',
            bargap=0.30, bargroupgap=0.6,
            title=dict(text="  <b>Naps</b> ", font=dict(color='#424149', family='Roboto', size=16)),
            xaxis=dict(dict(type='date')),
            xaxis_range=[start_range, end_range],
            yaxis_ticksuffix='m'
        )
    else:
        fig = go.Figure()
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.add_annotation(xref='paper', yref='paper',
                           text="Data Not Available",
                           font=dict(size=24, color="gray"),
                           showarrow=False, )
        fig.update_layout(
            plot_bgcolor="white",
            title=dict(text="  <b>Naps</b> ",
                       font=dict(color='#424149', family='Roboto', size=16)),
        )
    return fig


def generate_narcolepsy_sleep_latency_chart(data):
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="white",
        title=dict(text="  <b>Sleep Latency</b> ", font=dict(color='#424149', family='Roboto', size=16)),
    )

    if len(data) > 0:
        x = [parse(item['BedTime']).replace(tzinfo=None) for item in data]
        y = [item['Sleep Latency'] for item in data]
        mean_sleep = np.mean(y)
        start_range = x[0] + relativedelta(days=-3)
        end_range = x[-1] + relativedelta(days=+3)
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines+text+markers",
            name="Sleep Latency",
            text=y,
            textposition="bottom center",
            marker_color='#F17E5D',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=x,
            y=[mean_sleep] * len(x),
            name="MSL = " + str(mean_sleep) + " min",
            mode='lines',
            line = dict(shape = 'linear', color = 'rgb(102, 154, 247)', dash = 'dot'),
            connectgaps = True
        ))
        fig.update_traces(texttemplate='%{text:.2s}', textposition='top right')
        fig.update_layout(uniformtext_minsize=24)

        fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='lightgray', tickvals=x, tickformat='%d %b %H:%M')
        fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='white')
        fig.update_layout(
            xaxis=dict(dict(type='date')),
            xaxis_range=[start_range, end_range],
            yaxis_ticksuffix='m'
        )
    else:
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.add_annotation(xref='paper', yref='paper',
                           text="Data Not Available",
                           font=dict(size=24, color="gray"),
                           showarrow=False, )

    return fig


def generate_narcolepsy_rem_latency_chart(data):
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor="white",
        title=dict(text="  <b>REM Latency</b> ", font=dict(color='#424149', family='Roboto', size=16)),
    )

    if len(data) > 0:
        x = [parse(item['BedTime']).replace(tzinfo=None) for item in data]
        y = [int(item['REM Latency'])/60 for item in data]
        mean_rem = np.mean(y)
        start_range = x[0] + relativedelta(days=-3)
        end_range = x[-1] + relativedelta(days=+3)
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines+text+markers",
            name="REM Latency",
            text=y,
            textposition="bottom center",
            marker_color='#F17E5D',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=x,
            y=[mean_rem] * len(x),
            name="Mean REM L = " + str(mean_rem) + " min",
            mode='lines',
            line = dict(shape = 'linear', color = 'rgb(102, 154, 247)', dash = 'dot'),
            connectgaps = True
        ))
        fig.update_traces(texttemplate='%{text:.2s}', textposition='top right')
        fig.update_layout(uniformtext_minsize=24)

        fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='lightgray', tickvals=x, tickformat='%d %b %H:%M')
        fig.update_yaxes(showgrid=False, showline=True, linewidth=1, linecolor='black', gridcolor='white')
        fig.update_layout(
            xaxis=dict(dict(type='date')),
            xaxis_range=[start_range, end_range],
            yaxis_ticksuffix='m'
        )
    else:
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.add_annotation(xref='paper', yref='paper',
                           text="Data Not Available",
                           font=dict(size=24, color="gray"),
                           showarrow=False, )

    return fig