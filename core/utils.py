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


class DurationError(Exception):
    """Base exception for duration-related errors."""
    pass


class DurationMissingError(DurationError, TypeError):
    """Raised when duration value is missing (None or empty)."""

    def __init__(self):
        super().__init__("Duration value is missing or None.")


class DurationFormatError(DurationError, TypeError):
    """Raised when duration value is not a valid timedelta type."""

    def __init__(self, value):
        super().__init__(
            "Duration must be a timedelta instance, got {type_name} ({value!r}).".format(
                type_name=type(value).__name__,
                value=value,
            )
        )


def _validate_duration(duration):
    """
    Validate that the input is a valid timedelta.

    Accepts both :class:`datetime.timedelta` and
    :class:`django.utils.timezone.timedelta` (which is the same type).

    :param duration: the value to validate
    :returns: the validated timedelta, clamped to zero if negative
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    if duration is None:
        raise DurationMissingError()
    if not isinstance(duration, datetime.timedelta):
        raise DurationFormatError(duration)
    if duration.total_seconds() < 0:
        duration = datetime.timedelta(seconds=0)
    return duration


def duration_parts(duration, include_microseconds=False):
    """
    Get hours, minutes, seconds (and optionally microseconds) from a timedelta.

    Preserves full precision using ``total_seconds()`` (accounts for days and
    fractional seconds). Accepts both :class:`datetime.timedelta` and
    :class:`django.utils.timezone.timedelta`. Negative durations are clamped
    to zero.

    :param duration: a timedelta instance
    :param include_microseconds: if True, returns a 4-tuple with microseconds
    :returns: ``(hours, minutes, seconds)`` or ``(hours, minutes, seconds, microseconds)``
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    duration = _validate_duration(duration)
    total_seconds = duration.total_seconds()

    hours = int(total_seconds // 3600)
    remainder = total_seconds - hours * 3600
    minutes = int(remainder // 60)
    seconds_float = remainder - minutes * 60
    seconds = int(seconds_float)
    microseconds = int(round((seconds_float - seconds) * 1_000_000))

    if microseconds == 1_000_000:
        seconds += 1
        microseconds = 0
    if seconds == 60:
        minutes += 1
        seconds = 0
    if minutes == 60:
        hours += 1
        minutes = 0

    if include_microseconds:
        return hours, minutes, seconds, microseconds
    return hours, minutes, seconds


def duration_string(duration, precision="s"):
    """
    Format hours, minutes and seconds as a human-friendly string (e.g. "2
    hours, 25 minutes, 31 seconds") with precision to h = hours, m = minutes
    or s = seconds.

    - Zero durations are rendered using proper i18n plural forms.
    - Negative durations are clamped to zero before formatting.
    - Accepts both :class:`datetime.timedelta` and
      :class:`django.utils.timezone.timedelta`.

    :param duration: a timedelta instance
    :param precision: ``"h"``, ``"m"``, or ``"s"``
    :returns: formatted human-readable duration string
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    h, m, s = duration_parts(duration)

    parts = []
    if h > 0 or precision == "h":
        parts.append(
            ngettext("%(hours)s hour", "%(hours)s hours", h) % {"hours": h}
        )
    if precision != "h":
        if m > 0 or parts or precision == "m":
            if parts:
                parts.append(", ")
            parts.append(
                ngettext("%(minutes)s minute", "%(minutes)s minutes", m)
                % {"minutes": m}
            )
    if precision != "h" and precision != "m":
        if s > 0 or parts or precision == "s":
            if parts and parts[-1] != ", ":
                parts.append(", ")
            parts.append(
                ngettext("%(seconds)s second", "%(seconds)s seconds", s)
                % {"seconds": s}
            )

    return "".join(parts)


def duration_total_seconds(duration):
    """
    Return the total number of seconds contained in the duration, including
    fractional seconds (microsecond precision).

    :param duration: a timedelta instance
    :returns: total seconds as a float
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    duration = _validate_duration(duration)
    return duration.total_seconds()


def duration_to_minutes(duration):
    """
    Convert duration to total minutes (float, preserves sub-minute precision).

    :param duration: a timedelta instance
    :returns: total minutes as a float
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    return duration_total_seconds(duration) / 60.0


def duration_to_hours(duration):
    """
    Convert duration to total hours (float, preserves sub-hour precision).

    :param duration: a timedelta instance
    :returns: total hours as a float
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    return duration_total_seconds(duration) / 3600.0


def duration_string_short_hm(duration):
    """
    Format a short duration string without seconds, e.g. ``"2h30m"``.

    Intended for compact display on graphs. Always shows hours and minutes
    (even if zero).

    :param duration: a timedelta instance
    :returns: a string of the form ``XhXm``
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    h, m, s = duration_parts(duration)
    return "{}h{}m".format(h, m)


def duration_string_short_ms(duration):
    """
    Format a short duration string with minutes and seconds (and hours if
    present), e.g. ``"1h5m30s"`` or ``"5m30s"``.

    :param duration: a timedelta instance
    :returns: a compact string suitable for graph labels
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    h, m, s = duration_parts(duration)
    if h > 0:
        return "{}h{}m{}s".format(h, m, s)
    return "{}m{}s".format(m, s)


def duration_string_short_hms(duration):
    """
    Format a short duration string with hours, minutes and seconds, e.g.
    ``"1h5m30s"``.

    :param duration: a timedelta instance
    :returns: a compact string of the form ``XhXmXs``
    :raises DurationMissingError: if duration is None
    :raises DurationFormatError: if duration is not a timedelta instance
    """
    h, m, s = duration_parts(duration)
    return "{}h{}m{}s".format(h, m, s)


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
