import time
from datetime import datetime, timedelta, timezone

T0 = datetime(2019, 12, 10, 11, 12, 13, tzinfo=timezone.utc)
TS = str(time.mktime(T0.timetuple()))


def T(offset):
    return str(T0 + timedelta(seconds=offset))
