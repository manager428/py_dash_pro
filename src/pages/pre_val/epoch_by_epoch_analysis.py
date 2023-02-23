
from . import config as config
from . constants import  Constants
from utilities.sleep_staging_result import SleepStagingResult, SleepStagingPrediction
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, cohen_kappa_score
from imblearn.metrics import specificity_score
import pandas as pd
import numpy as np
import math

if config.num_output == 2:
    STAGES = ['Wake', 'Sleep']
elif config.num_output == 3:
    STAGES = ['Wake', 'NREM', 'REM']
elif config.num_output == 4:
    STAGES = ['Wake', 'Light', 'Deep', 'REM']


def main(users_dict):
    """
    user_dict = {'user1': [psg_df, device_df], 'user2': [psg_df, device_df], ...}
    psg_df = DataFrame{'time', 'stage'}
    device_df = DataFrame{'time', 'stage'}
    """
    result_obj_tib_intersection = generate_result_obj(users_dict, 'intersection')
    result_obj_tib_union = generate_result_obj(users_dict, 'union')
    return group_level_performance(result_obj_tib_intersection), group_level_performance(result_obj_tib_union)


def generate_result_obj(users_dict, mode):
    result_obj = SleepStagingResult()
    result_obj.true_labels = []
    result_obj.prediction_dict['device'] = SleepStagingPrediction([], [])
    # what to do with the data loss?
    for df_list in users_dict.values():
        psg_df, device_df = df_list
        if mode == 'intersection':
            device_stages, psg_stages = find_intersection_of_stages(psg_df, device_df)
        elif mode == 'union':
            device_stages, psg_stages = find_stage_union(psg_df, device_df)
        result_obj.true_labels += psg_stages
        result_obj.prediction_dict['device'].predicted_labels += device_stages
    return result_obj


def find_intersection_of_stages(psg_df, device_df):
    """
    the goal is to find epochs that are limited to the PSG TIB
    """
    device_stages = []
    psg_stages = []

    for i, time in enumerate(device_df['time']):
        indices = psg_df[(psg_df['time'] >= time) & (psg_df['time'] < (time + Constants.EPOCH_DURATION_IN_SECONDS))].index
        if len(indices) > 0:
            device_stages.append(device_df.loc[i, 'stage'])
            psg_stages.append(psg_df.loc[indices[0], 'stage'])
    return device_stages, psg_stages


def find_stage_union(psg_df, device_df):
    """
    The assumption here is the epochs beyond TIB are Wake. The total epochs are based on
    the union of PSG TIB and device TIB.
    """
    device_stages = []
    psg_stages = []


    # find the union interval
    device_start_epoch = device_df.time[0]
    device_end_epoch = device_df.time[len(device_df) - 1]
    psg_start_epoch = psg_df.time[0]
    psg_end_epoch = psg_df.time[len(psg_df) - 1]
    start = min(device_start_epoch, psg_start_epoch)
    end = max(device_end_epoch, psg_end_epoch)

    # prepare the stages to have the same length and proper value
    for epoch in np.arange(start, end + Constants.EPOCH_DURATION_IN_SECONDS, Constants.EPOCH_DURATION_IN_SECONDS):
        psg_indices = psg_df[(psg_df['time'] >= epoch) & (psg_df['time'] < (epoch + Constants.EPOCH_DURATION_IN_SECONDS))].index
        device_indices = device_df[(device_df['time'] >= epoch) & (device_df['time'] < (epoch + Constants.EPOCH_DURATION_IN_SECONDS))].index

        if len(device_indices) > 0:
            device_stages.append(device_df.loc[device_indices[0], 'stage'])
        else:
            device_stages.append(0)  # add wake=0 if the epoch is not in the device hypnogram

        if len(psg_indices) > 0:
            psg_stages.append(psg_df.loc[psg_indices[0], 'stage'])
        else:
            psg_stages.append(0)  # add wake=0 if the epoch is not in the psg hypnogram
    return device_stages, psg_stages


def group_level_performance(all_concat_result):
    performance_df = pd.DataFrame(
        columns=['Stage', 'Device', 'Accuracy', 'Sensitivity', 'Specificity', 'Precision', 'F1_score',
                 'Cohen_Kappa'])
    i = 0
    for device in all_concat_result.prediction_dict.keys():
        performance_stage = calc_performance(all_concat_result, device, None)
        performance_stage = list(zip(*performance_stage))
        for ind, stage in enumerate(STAGES):
            performance_df.loc[i] = [stage, device] + list(performance_stage[ind]) + [math.nan]
            i += 1

        average = 'macro'
        if len(STAGES) == 2:
            average = 'binary'

        performance_night = calc_performance(all_concat_result, device, average)
        performance_df.loc[i] = ['Night', device] + performance_night
        i += 1
    return performance_df


def calc_performance(result_obj, classifier_name, averaging_type):
    performance = []
    performance.append(calc_accuracy(result_obj, classifier_name, averaging_type))
    performance.append(calc_sensitivity(result_obj, classifier_name, averaging_type))
    performance.append(calc_specificity(result_obj, classifier_name, averaging_type))
    performance.append(calc_precision(result_obj, classifier_name, averaging_type))
    performance.append(calc_f1score(result_obj, classifier_name, averaging_type))
    if averaging_type:
        performance.append(calc_cohen(result_obj, classifier_name))

    if averaging_type:
        return [round(100 * value, 2) for value in performance]
    else:
        return [[round(100 * value, 2) for value in element] for element in performance]


def calc_accuracy(sleep_staging_result, device, averaging_type='macro'):
    true_label = sleep_staging_result.true_labels
    pred_label = sleep_staging_result.prediction_dict[device].predicted_labels
    if averaging_type is 'macro' or averaging_type is 'binary':
        return accuracy_score(true_label, pred_label)
    else:
        return [accuracy_score([int(i != j) for i in true_label], [int(i != j) for i in pred_label]) for j in
                range(config.num_output)]


def calc_specificity(sleep_staging_result, device, averaging_type='macro'):
    return specificity_score(sleep_staging_result.true_labels,
                             sleep_staging_result.prediction_dict[device].predicted_labels,
                             average=averaging_type)


def calc_sensitivity(sleep_staging_result, device, averaging_type='macro'):
    return recall_score(sleep_staging_result.true_labels,
                        sleep_staging_result.prediction_dict[device].predicted_labels,
                        average=averaging_type)


def calc_precision(sleep_staging_result, device, averaging_type='macro'):
    return precision_score(sleep_staging_result.true_labels,
                           sleep_staging_result.prediction_dict[device].predicted_labels,
                           average=averaging_type)


def calc_f1score(sleep_staging_result, device, averaging_type='macro'):
    return f1_score(sleep_staging_result.true_labels,
                    sleep_staging_result.prediction_dict[device].predicted_labels,
                    average=averaging_type)


def calc_cohen(sleep_staging_result, device):
    return cohen_kappa_score(sleep_staging_result.true_labels,
                             sleep_staging_result.prediction_dict[device].predicted_labels,
                             weights='quadratic')



