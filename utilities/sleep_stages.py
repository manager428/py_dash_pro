from enum import Enum


class SleepStages(Enum):
    unlabeled = -1
    unscored = -1
    wake = 0
    n1 = 1
    n2 = 2
    n3 = 3
    n4 = 4
    rem = 5


