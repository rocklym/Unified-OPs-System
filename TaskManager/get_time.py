# coding=utf-8

import re
import time

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


# 获取当前时间戳
def current_timestamp():
    return time.time()


# 获取当前年月日
def current_ymd():
    return time.strftime("%Y%m%d")


# 获取当前年月日-时分秒
def current_ymd_hms():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def format_datetime(trigger_time, earliest, latest):
    # 年-月-日 时:分:秒
    ymd_hms_pattern = re.compile(
        ur'((((1[6-9]|[2-9]\d)\d{2})-(1[02]|0?[13578])-([12]\d|3[01]|0?[1-9]))|(((1[6-9]|[2-9]\d)\d{2})-'
        ur'(1[012]|0?[13456789])-([12]\d|30|0?[1-9]))|(((1[6-9]|[2-9]\d)\d{2})-0?2-(1\d|2[0-8]|0?[1-9]))|'
        ur'(((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|((16|[2468][048]|[3579][26])00))-0?2-29-)) '
        ur'([01]?\d|2[0-3]):[0-5]?\d(:[0-5]?\d)?')
    hms_pattern = re.compile(ur'([01]?\d|2[0-3]):[0-5]?\d(:[0-5]?\d)?')
    current_datetime = parse(current_ymd_hms())
    temp = parse("{0}-{1}-{2}".format(current_datetime.year, current_datetime.month, current_datetime.day))
    if trigger_time and hms_pattern.search(trigger_time):
        if ymd_hms_pattern.search(trigger_time):
            trigger_datetime = parse(trigger_time)
        else:
            trigger_datetime = parse(
                "{0}-{1}-{2} {3}:{4}:{5}".format(temp.year, temp.month, temp.day, int(trigger_time.split(":")[0]),
                                                 int(trigger_time.split(":")[1]), 0))
    else:
        trigger_datetime = None
    if earliest and hms_pattern.search(earliest):
        earliest_datetime = parse(
            "{0}-{1}-{2} {3}:{4}:{5}".format(temp.year, temp.month, temp.day, int(earliest.split(":")[0]),
                                             int(earliest.split(":")[1]), 0))
        if trigger_datetime > earliest_datetime:
            earliest_datetime = earliest_datetime + relativedelta(days=1)
    else:
        earliest_datetime = None
    if latest and hms_pattern.search(latest):
        latest_datetime = parse(
            "{0}-{1}-{2} {3}:{4}:{5}".format(temp.year, temp.month, temp.day, int(latest.split(":")[0]),
                                             int(latest.split(":")[1]), 0))
        if trigger_datetime > latest_datetime:
            latest_datetime = latest_datetime + relativedelta(days=1)
    else:
        latest_datetime = None
    return current_datetime, earliest_datetime, latest_datetime


def compare_timestamps(trigger_time, earliest, latest):
    current_datetime, earliest_datetime, latest_datetime = format_datetime(trigger_time, earliest, latest)
    if not earliest_datetime and not latest_datetime:
        return 1, None
    if not earliest_datetime and latest_datetime:
        if latest_datetime >= current_datetime:
            return 1, None
        else:
            return 3, None
    if not latest_datetime and earliest_datetime:
        if earliest_datetime <= current_datetime:
            return 1, None
        else:
            return 2, (earliest_datetime - current_datetime).seconds
    if earliest_datetime and latest_datetime:
        if earliest_datetime > latest_datetime:
            return 3, None
        if current_datetime > latest_datetime:
            return 3, None
        if current_datetime < earliest_datetime:
            return 2, (earliest_datetime - current_datetime).seconds
        if earliest_datetime < current_datetime < latest_datetime:
            return 1, None
