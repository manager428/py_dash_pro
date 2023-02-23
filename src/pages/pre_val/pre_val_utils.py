import math
import datetime
import pandas as pd
import numpy as np
from dateutil.parser import parse
import boto3
from boto3.dynamodb.conditions import Key

from src import application
from src.libs.utils import custom_date_parser, download_csv_file

dynamodb = boto3.resource('dynamodb')
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE']) 

s3client = boto3.client('s3')
s3_bucket_name = application.config['S3_PROCESSED_BUCKET']


def get_night_folders_tab2(username ,divice,start_date,end_date):
    night_folders = []  

    path_to_s3_processed = s3_bucket_name +divice+ '/'+ username

    resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix=divice+'/'+username+'/', Delimiter="/")
    
    folders = [x['Prefix'].split('/')[2] for x in resp['CommonPrefixes']]
    
    for rec_folder in folders:
        try:
            recording_date = custom_date_parser(rec_folder).date()
            if( parse(start_date).date() <= recording_date <= parse(end_date).date()):
                night_folders.append({'path':path_to_s3_processed,'night':rec_folder})    
        except Exception as e:
            print (e)  

    return night_folders   

def get_sleep_data(username):
    sleep_response = db_table.query(
                KeyConditionExpression=Key('PK').eq("USER#{}".format(username)) &  Key('SK').begins_with("#SLEEP#")
        )
    sleep_data = {}  
    kss_data = {}
    naps_data = {}   
    for data in sleep_response['Items']: 
        if not 'awakening' in data['SK'] and not 'nap' in data['SK'] and not 'kss' in data['SK']:
            date_str = data['SK'].split('#')[2]
            date = parse(date_str).date() 
            sleep_data[date] = data 
    for data in sleep_response['Items']: 
        if  'kss' in data['SK'] :
            date_str = data['SK'].split('#')[2]
            start_time = datetime.datetime.strptime(data['start'], '%Y-%m-%dT%H:%M:%S%z').time()
            start_time = datetime.datetime.combine(parse(date_str).date(), start_time)
            kss_data[start_time] = int(data['R'])
    for data in sleep_response['Items']: 
        if  'nap' in data['SK'] :
            date_str = data['SK'].split('#')[2]
            date = parse(date_str).date() 
            naps_data[date] = data        
        
    return sleep_data, kss_data, naps_data

def get_user_details(username):
    response = db_table.query(
                IndexName='InvertedIndex',
                KeyConditionExpression=Key('SK').eq("#METADATA#{}".format(username))
        )
    return response['Items'][0]

def get_user_que_ans(username):

    user_que_ans = {'cr' : [],'ins' : [],'eds': [],'sa':[]}

    try:
        qa_response = db_table.query(
                KeyConditionExpression=Key('PK').eq("USER#{}".format(username)) &  Key('SK').begins_with("#COMPLAINT")
        )    
        qa_detail=qa_response['Items']
        for qa in qa_detail :
            if 'cr' in qa['SK'] :
                user_que_ans['cr'].append(qa)
            if 'ins' in qa['SK'] :
                user_que_ans['ins'].append(qa)
            if 'eds' in qa['SK'] :
                user_que_ans['eds'].append(qa)
            if 'sa' in qa['SK'] :
                user_que_ans['sa'].append(qa)        
    except Exception as e:
        pass

    return user_que_ans

def get_user_age(row):
        try:
            user_details = get_user_details(row['ID'])
            dob = datetime.datetime.strptime(user_details['dob'], '%d%m%Y').date()
            today = datetime.date.today() 
            extra_year = 1 if ((today.month, today.day) < (dob.month, dob.day)) else 0
            return  today.year - dob.year - extra_year
        except Exception as e :
            return None

def get_user_gender(row):
    try:
        user_details = get_user_details(row['ID'])
        return user_details['gender']
    except Exception as e :
        return None     

def df_efficiency_to_int(df):
    eff_val_in_str = df.loc[df['Metric'] == 'Efficiency', 'Value'].values[0].split('%')[0]
    df.loc[df['Metric'] == 'Efficiency', 'Value'] = eff_val_in_str   
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    return df

def difference_in_sleep_diary_and_algorithm(sleep_df, algorithm_df):
    
    sleep_dates = sleep_df['date'].to_list()
    individual_dates_diff = {}
    for date in sleep_dates:
        date_midnight = datetime.datetime.combine(date, datetime.datetime.min.time())
        date_noon_time = date_midnight + datetime.timedelta(hours=12)
        next_day_noon_time = date_midnight + datetime.timedelta(hours=35, minutes=59)
        algorithm_df['bedtine_date'] = algorithm_df.apply(lambda row: parse(row['BedTime']) , axis=1)
        mask = (date_noon_time <= algorithm_df['bedtine_date']) & (algorithm_df['bedtine_date'] <= next_day_noon_time )
        rows_in_multi_day = algorithm_df.loc[mask]
        if len(rows_in_multi_day) > 0:
            print (len(rows_in_multi_day))
            date_str = str(date)
            individual_dates_diff[date_str] = {}
            values_in_file = sleep_df[sleep_df['date']==date].iloc[0].to_dict()
            # find row with max sleep time
            values_in_multi_day = rows_in_multi_day[rows_in_multi_day['TST'] == rows_in_multi_day['TST'].max()].iloc[0].to_dict()
            bedtime_in_file = values_in_file['BedTime']
            bedtime_in_multiday = parse(values_in_multi_day['BedTime']) 
            sleeponset_in_file = values_in_file['SleepOnset']
            sleeponset_in_multiday = parse(values_in_multi_day['SleepOnset'])
            sleepoffset_in_file = values_in_file['SleepOffset']
            sleepoffset_in_multiday = parse(values_in_multi_day['SleepOffset'])
            outofbed_in_file = values_in_file['OutOfBed']
            outofbed_in_multiday = parse(values_in_multi_day['OutOfBedTime'])
    
            if bedtime_in_file > bedtime_in_multiday:
                individual_dates_diff[date_str]['BedTime_Diff'] = round((bedtime_in_file-bedtime_in_multiday).seconds/60, 2)  
            else: 
                individual_dates_diff[date_str]['BedTime_Diff'] = round(((bedtime_in_multiday-bedtime_in_file).seconds/60)*(-1), 2)  
            if sleeponset_in_file > sleeponset_in_multiday:
                individual_dates_diff[date_str]['SleepOnset_Diff'] = round((sleeponset_in_file-sleeponset_in_multiday).seconds/60, 2)   
            else: 
                individual_dates_diff[date_str]['SleepOnset_Diff'] = round(((sleeponset_in_multiday-sleeponset_in_file).seconds/60)*(-1), 2)  
            if sleepoffset_in_file > sleepoffset_in_multiday:
                individual_dates_diff[date_str]['SleepOffSet_Diff'] = round((sleepoffset_in_file-sleepoffset_in_multiday).seconds/60, 2)    
            else: 
                individual_dates_diff[date_str]['SleepOffSet_Diff'] = round(((sleepoffset_in_multiday-sleepoffset_in_file).seconds/60)*(-1), 2)  
            if outofbed_in_file > outofbed_in_multiday:
                individual_dates_diff[date_str]['OutOfBed_Diff'] = round((outofbed_in_file-outofbed_in_multiday).seconds/60, 2)   
            else: 
                individual_dates_diff[date_str]['OutOfBed_Diff'] = round(((outofbed_in_multiday-outofbed_in_file).seconds/60)*(-1), 2) 
    return get_statics_of_diff_in_sleep_diary_and_algorithm(individual_dates_diff)            
    
def get_statics_of_diff_in_sleep_diary_and_algorithm(individual_diffs):
    bedtime_diff_list = [abs(val['BedTime_Diff']) for key , val in individual_diffs.items()]
    sleeponset_diff_list = [abs(val['SleepOnset_Diff']) for key , val in individual_diffs.items()]
    sleepoffset_diff_list = [abs(val['SleepOffSet_Diff']) for key , val in individual_diffs.items()]
    outofbedtime_diff_list = [abs(val['OutOfBed_Diff']) for key , val in individual_diffs.items()]
    individual_diffs['Total']={} 
    individual_diffs['Total']['BedTime_Diff']=round(sum(([x for x in bedtime_diff_list if not math.isnan(x)])), 2)
    individual_diffs['Total']['SleepOnset_Diff']=round(sum(([x for x in sleeponset_diff_list if not math.isnan(x)])), 2) 
    individual_diffs['Total']['SleepOffSet_Diff']=round(sum(([x for x in sleepoffset_diff_list if not math.isnan(x)])), 2) 
    individual_diffs['Total']['OutOfBed_Diff']=round(sum(([x for x in outofbedtime_diff_list if not math.isnan(x)])), 2)  
    individual_diffs['Min']={} 
    individual_diffs['Min']['BedTime_Diff']= round(min([x for x in bedtime_diff_list if not math.isnan(x)], default=0.0), 2)  
    individual_diffs['Min']['SleepOnset_Diff']=round(min([x for x in sleeponset_diff_list if not math.isnan(x)],default=0.0), 2)  
    individual_diffs['Min']['SleepOffSet_Diff']=round(min([x for x in sleepoffset_diff_list if not math.isnan(x)],default=0.0), 2)  
    individual_diffs['Min']['OutOfBed_Diff']=round(min([x for x in outofbedtime_diff_list if not math.isnan(x)],default=0.0), 2) 
    individual_diffs['Max']={} 
    individual_diffs['Max']['BedTime_Diff']=round(max(([x for x in bedtime_diff_list if not math.isnan(x)])), 2)  
    individual_diffs['Max']['SleepOnset_Diff']=round(max(([x for x in sleeponset_diff_list if not math.isnan(x)])), 2)  
    individual_diffs['Max']['SleepOffSet_Diff']= round(max(([x for x in sleepoffset_diff_list if not math.isnan(x)])) ,2)
    individual_diffs['Max']['OutOfBed_Diff']=round(max(([x for x in outofbedtime_diff_list if not math.isnan(x)])), 2) 
    individual_diffs['Mean']={} 
    individual_diffs['Mean']['BedTime_Diff']=round(np.mean(([x for x in bedtime_diff_list if not math.isnan(x)])), 2)  
    individual_diffs['Mean']['SleepOnset_Diff']=round(np.mean(([x for x in sleeponset_diff_list if not math.isnan(x)])), 2)  
    individual_diffs['Mean']['SleepOffSet_Diff']= round(np.mean(([x for x in sleepoffset_diff_list if not math.isnan(x)])) ,2)
    individual_diffs['Mean']['OutOfBed_Diff']=round(np.mean(([x for x in outofbedtime_diff_list if not math.isnan(x)])), 2) 
    individual_diffs['Median']={}
    individual_diffs['Median']['BedTime_Diff']=round(np.median(([x for x in bedtime_diff_list if not math.isnan(x)])), 2)
    individual_diffs['Median']['SleepOnset_Diff']=round(np.median(([x for x in sleeponset_diff_list if not math.isnan(x)])), 2)
    individual_diffs['Median']['SleepOffSet_Diff']=round(np.median(([x for x in sleepoffset_diff_list if not math.isnan(x)])), 2)
    individual_diffs['Median']['OutOfBed_Diff']=round(np.median(([x for x in outofbedtime_diff_list if not math.isnan(x)])), 2)
     
    return individual_diffs

def get_recordings_from_mslt(night_folder):
    all_labels = []
    all_times = []
    all_awakeings = []
    all_hr = []
    all_activity = []
    all_sleep=[]
    all_sleep_metrics=[]

    mslt_recordings = {}

    try:

        path_to_s3_processed = night_folder

        next_hr = True
        hr_no = 1
        while  next_hr:
            hr = download_csv_file(path_to_s3_processed + '/heartrate_{}.csv'.format(hr_no))
            if hr is not None :
                all_hr.append(hr)
                hr_no+=1
            else:
                next_hr = False

        next_label = True
        label_no = 1
        while  next_label:
            labels = download_csv_file(path_to_s3_processed + '/stage_prediction_{}.csv'.format(label_no))
            if  labels is not None :
                all_labels.append(labels['labels'])
                label_no+=1
            else:
                next_label = False

        next_time = True
        time_no = 1
        while  next_time:
            times = download_csv_file(path_to_s3_processed + '/epoch_time_{}.csv'.format(time_no))
            if times is not None :
                all_times.append(times)
                time_no+=1
            else:
                next_time = False

        next_awakeing = True
        awakeing_no = 1
        while  next_awakeing:
            awakeings = download_csv_file(path_to_s3_processed + '/awakenings_{}.csv'.format(awakeing_no))
            if awakeings is not None :
                all_awakeings.append(awakeings)
                awakeing_no+=1
            else:
                next_awakeing = False
        
        next_sleep_metrics= True
        sleep_metrics_no = 1
        while  next_sleep_metrics:
            sleep_metrics = download_csv_file(path_to_s3_processed + '/sleep_metrics_{}.csv'.format(sleep_metrics_no))
            if sleep_metrics is not None :
                all_sleep_metrics.append(sleep_metrics)
                sleep_metrics_no+=1
            else:
                next_sleep_metrics = False        

    except Exception as e:
        print ("err in getting mslt recordings",e)

    mslt_recordings['sleep'] = all_sleep
    mslt_recordings['activity'] = all_activity
    mslt_recordings['hrs'] = all_hr
    mslt_recordings['labels'] = all_labels
    mslt_recordings['awakeings'] = all_awakeings
    mslt_recordings['times'] = all_times
    mslt_recordings['sleep_metrics'] = all_sleep_metrics

    return mslt_recordings

def get_pre_next_rec(username ,divice,night_folder):

    resp = s3client.list_objects(Bucket=s3_bucket_name.split("/")[2], Prefix=divice+'/'+username+'/', Delimiter="/")
    
    folders = [x['Prefix'].split('/')[2] for x in resp['CommonPrefixes']]
    sorted_list = sorted(folders)
    night_folder_idx = sorted_list.index(night_folder)

    return sorted_list[night_folder_idx-1] , sorted_list[night_folder_idx+1]

def get_statics_from_multi_day(sleep_df, algorithm_df):
    sleep_dates = sleep_df['date'].to_list()
    indexes = []
    multi_day_statics = []
    for date in sleep_dates:
        date_midnight = datetime.datetime.combine(date, datetime.datetime.min.time())
        date_noon_time = date_midnight + datetime.timedelta(hours=12)
        next_day_noon_time = date_midnight + datetime.timedelta(hours=35, minutes=59)
        algorithm_df['bedtine_date'] = algorithm_df.apply(lambda row: parse(row['BedTime']) , axis=1)
        mask = (date_noon_time <= algorithm_df['bedtine_date']) & (algorithm_df['bedtine_date'] <= next_day_noon_time )
        rows_in_multi_day = algorithm_df.loc[mask]
        if len(rows_in_multi_day) > 0:
            # find row with max sleep time
            row_with_max = rows_in_multi_day[rows_in_multi_day['TST'] == rows_in_multi_day['TST'].max()]
            indexes.append(row_with_max.index[0])

    filtered_algorithm_df = algorithm_df.iloc[indexes]   
    filtered_algorithm_df['Efficiency'] = filtered_algorithm_df['Efficiency'].apply(lambda eff : float(eff.split('%')[0])) 

    multi_day_statics.append({  'Metric':'TST','max': int(filtered_algorithm_df['TST'].max()), 
                                'min':int (filtered_algorithm_df['TST'].min()), 
                                'mean': int(filtered_algorithm_df['TST'].mean()),
                                'median':int(filtered_algorithm_df['TST'].median())
                            })
    multi_day_statics.append({  'Metric':'REM Time','max': int(filtered_algorithm_df['REM Time'].max()), 
                                'min': int(filtered_algorithm_df['REM Time'].min()) , 
                                'mean': int(filtered_algorithm_df['REM Time'].mean()),
                                'median':int(filtered_algorithm_df['REM Time'].median())
                            })
    multi_day_statics.append({  'Metric':'NREM Time','max':int(filtered_algorithm_df['NREM Time'].max()), 
                                'min': int(filtered_algorithm_df['NREM Time'].min()) , 
                                'mean': int(filtered_algorithm_df['NREM Time'].mean())
                            })
    multi_day_statics.append({  'Metric':'NREM Time','max':int(filtered_algorithm_df['NREM Time'].max()), 
                                'min': int(filtered_algorithm_df['NREM Time'].min()), 
                                'mean': int(filtered_algorithm_df['NREM Time'].mean()), 
                                'median':int(filtered_algorithm_df['NREM Time'].median())
                            }) 
    multi_day_statics.append({  'Metric':'Wake Time','max':int(filtered_algorithm_df['Wake Time'].max()), 
                                'min': int(filtered_algorithm_df['Wake Time'].min()), 
                                'mean': int(filtered_algorithm_df['Wake Time'].mean()), 
                                'median':int(filtered_algorithm_df['Wake Time'].median())
                            }) 
    multi_day_statics.append({  'Metric':'TIB','max':int(filtered_algorithm_df['TIB'].max()), 
                                'min': int(filtered_algorithm_df['TIB'].min()), 
                                'mean': int(filtered_algorithm_df['TIB'].mean()), 
                                'median':int(filtered_algorithm_df['TIB'].median())
                            })
    multi_day_statics.append({  'Metric':'WASO','max':int(filtered_algorithm_df['WASO'].max()), 
                                'min': int(filtered_algorithm_df['WASO'].min()) , 
                                'mean': int(filtered_algorithm_df['WASO'].mean()), 
                                'median':int(filtered_algorithm_df['WASO'].median())
                            })
    multi_day_statics.append({  'Metric':'Awakenings','max':int(filtered_algorithm_df['Awakenings'].max()), 
                                'min': int(filtered_algorithm_df['Awakenings'].min()), 
                                'mean': int(filtered_algorithm_df['Awakenings'].mean()),
                                'median':int(filtered_algorithm_df['Awakenings'].median())
                         })
    multi_day_statics.append({  'Metric':'Sleep Latency','max':int(filtered_algorithm_df['Sleep Latency'].max()), 
                                'min': int(filtered_algorithm_df['Sleep Latency'].min()),
                                'mean': int(filtered_algorithm_df['Sleep Latency'].mean()), 
                                'median':int(filtered_algorithm_df['Sleep Latency'].median())
                         })
    multi_day_statics.append({  'Metric':'REM Latency','max':int(filtered_algorithm_df['REM Latency'].max()), 
                                'min': int(filtered_algorithm_df['REM Latency'].min()),
                                'mean': int(filtered_algorithm_df['REM Latency'].mean()), 
                                'median':int(filtered_algorithm_df['REM Latency'].median())
                            })
    multi_day_statics.append({  'Metric':'Efficiency','max':float(filtered_algorithm_df['Efficiency'].max()), 
                                'min': float(filtered_algorithm_df['Efficiency'].min()), 
                                'mean': float("{0:.2f}".format(filtered_algorithm_df['Efficiency'].mean())), 
                                'median':float("{0:.2f}".format(filtered_algorithm_df['Efficiency'].median()))
                            })                                                                                                                                                                                                                                                                                                  
    return multi_day_statics   