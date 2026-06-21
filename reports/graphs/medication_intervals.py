# -*- coding: utf-8 -*-
from django.db.models import Count
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_to_hours, duration_string_short_hms

from reports import utils


def medication_intervals(instances):
    """
    Create a graph showing intervals of medication instances over time.

    :param instances: a QuerySet of Medication instances.
    :returns: a tuple of the graph's html and javascript.
    """
    totals = instances.annotate(count=Count("id")).order_by("time")

    if not totals.exists():
        return None, None

    intervals = []
    last_medication = totals.first()
    for medication in totals[1:]:
        interval = medication.time - last_medication.time
        if interval.total_seconds() > 0:
            intervals.append(interval)
        last_medication = medication

    if not intervals:
        return None, None

    trace_avg = go.Scatter(
        name=_("Interval"),
        line=dict(shape="spline"),
        x=list(totals.values_list("time", flat=True)[1:]),
        y=[duration_to_hours(i) for i in intervals],
        hoverinfo="text",
        text=[duration_string_short_hms(i) for i in intervals],
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Medication intervals") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace_avg.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Medication interval (hours)")

    fig = go.Figure({"data": [trace_avg], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
