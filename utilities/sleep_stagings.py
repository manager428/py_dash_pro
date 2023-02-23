from enum import Enum


class ThreeClassLabel(Enum):
    wake = 0
    rem = 1
    nrem = 2


class FourClassLabel(Enum):
    wake = 0
    light = 1
    deep = 2
    rem = 3


class LabelConverter:

    @classmethod
    def convert_labels(cls, num_class_choice, labels):
        if num_class_choice == len(ThreeClassLabel):
            return cls.convert_to_three_class(labels)
        elif num_class_choice == len(FourClassLabel):
            return cls.convert_to_four_class(labels)

    @staticmethod
    def convert_to_three_class(old_labels):
        converted_labels = []
        for label in old_labels:

            if label == 0:
                converted_labels.append(ThreeClassLabel.wake.value)

            elif 1 <= label <= 4:
                converted_labels.append(ThreeClassLabel.nrem.value)

            elif label >= 5:
                converted_labels.append(ThreeClassLabel.rem.value)
        return converted_labels

    @staticmethod
    def convert_to_four_class(old_labels):
        converted_labels = []
        for label in old_labels:

            if label == 0:
                converted_labels.append(FourClassLabel.wake.value)

            elif label == 1 or label == 2:
                converted_labels.append(FourClassLabel.light.value)

            elif label == 3 or label == 4:
                converted_labels.append(FourClassLabel.deep.value)

            elif label > 5:
                converted_labels.append(FourClassLabel.rem.value)
        return converted_labels

    @staticmethod
    def three_class_int_to_label(labels):
        string = []
        int_to_string = {
            0: ThreeClassLabel.wake.name,
            1: ThreeClassLabel.nrem.name,
            2: ThreeClassLabel.rem.name}
        for label in labels:
            string.append(int_to_string[label])
        return string

    @staticmethod
    def four_class_int_to_label(labels):
        string = []
        int_to_string = {
            0: FourClassLabel.wake.name,
            1: FourClassLabel.light.name,
            2: FourClassLabel.deep.name,
            3: FourClassLabel.rem.name}
        for label in labels:
            string.append(int_to_string[label])
        return string
