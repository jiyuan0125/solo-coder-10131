# -*- coding: utf-8 -*-
import datetime
import random

from django.utils import timezone
from django.utils.translation import ngettext

random.seed()

COLORS = [
    "#ff0000",
    "#00ff00",
    "#0000ff",
    "#ff00ff",
    "#ffff00",
    "#00ffff",
    "#ff7f7f",
    "#7fff7f",
    "#7f7fff",
    "#ff7fff",
    "#ffff7f",
    "#7fffff",
    "#7f0000",
    "#007f00",
    "#00007f",
    "#7f007f",
    "#7f7f00",
    "#007f7f",
]


def _validate_duration(duration, allow_none=False):
    """
    Validate that duration is a timedelta (both stdlib datetime.timedelta and
    django.utils.timezone.timedelta are accepted since they are the same type).
    Raises TypeError with a clear message distinguishing type errors from
    missing values.
    """
    if duration is None:
        if allow_none:
            return None
        raise TypeError(
            "Duration value is missing (None). Expected a timedelta instance."
        )
    if not isinstance(duration, datetime.timedelta):
        raise TypeError(
            "Duration must be a timedelta instance, got {} instead.".format(
                type(duration).__name__
            )
        )
    return duration


def duration_parts(duration, allow_negative=False):
    """
    Get hours, minutes, seconds and microseconds from a timedelta.
    Accepts both datetime.timedelta and django.utils.timezone.timedelta.
    Negative durations are clamped to zero unless allow_negative=True.
    Returns a tuple of (hours, minutes, seconds, microseconds).
    """
    duration = _validate_duration(duration)
    if not allow_negative and duration.total_seconds() < 0:
        duration = datetime.timedelta(0)
    total_seconds = duration.total_seconds()
    h = int(total_seconds // 3600)
    remainder = total_seconds - h * 3600
    m = int(remainder // 60)
    s = int(remainder - m * 60)
    us = duration.microseconds
    return h, m, s, us


def duration_string(duration, precision="s"):
    """
    Format hours, minutes and seconds as a human-friendly string
    (e.g. "2 hours, 25 minutes, 31 seconds") with precision to
    h = hours, m = minutes or s = seconds.
    Uses i18n pluralization rules correctly including for zero values.
    Accepts both datetime.timedelta and django.utils.timezone.timedelta.
    Negative durations are clamped to zero.
    """
    h, m, s, _ = duration_parts(duration)

    result = ""
    if h > 0:
        result = ngettext("%(hours)s hour", "%(hours)s hours", h) % {"hours": h}
    if precision != "h":
        if result != "":
            result += ", "
        result += ngettext("%(minutes)s minute", "%(minutes)s minutes", m) % {
            "minutes": m
        }
    if s > 0 and precision != "h" and precision != "m":
        if result != "":
            result += ", "
        result += ngettext("%(seconds)s second", "%(seconds)s seconds", s) % {
            "seconds": s
        }

    return result


def duration_total_seconds(duration):
    """
    Get total seconds from a timedelta with microsecond precision preserved.
    Accepts both datetime.timedelta and django.utils.timezone.timedelta.
    Negative durations return 0.
    """
    duration = _validate_duration(duration)
    total = duration.total_seconds()
    return total if total >= 0 else 0


def random_color():
    return COLORS[random.randrange(0, len(COLORS))]


def timezone_aware_duration(
    start: timezone.datetime, end: timezone.datetime
) -> datetime.timedelta:
    """
    Calculate a duration between timezone aware dates in UTC. This accounts for DST changes between dates.
    """
    utc = datetime.timezone.utc
    return end.astimezone(utc) - start.astimezone(utc)
