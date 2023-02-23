

class SleepStagingPrediction:
    def __init__(self, probability, predicted_labels):
        self.probability = probability
        self.predicted_labels = predicted_labels


class SleepStagingResult:
    def __init__(self, subject_id=None, true_labels=None):
        self.subject_id = subject_id
        self.true_labels = true_labels
        self.prediction_dict = {}  # {classifier_name:SleepStagingPrediction}