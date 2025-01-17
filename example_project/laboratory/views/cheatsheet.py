"""Views for displaying examples of manipulating experimental device's field value outputs."""

from django.template.response import TemplateResponse

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintMax
from django_pint_field.aggregates import PintMin
from django_pint_field.aggregates import PintSum
from example_project.laboratory.models import ExperimentalDevice


def cheatsheet(request) -> TemplateResponse:
    """Display comprehensive examples of manipulating field value outputs in templates."""
    template = "laboratory/cheatsheet/cheatsheet.html"

    # Get the first device
    device = ExperimentalDevice.objects.first()
    field = device._meta.get_field("portal_diameter")

    # Get aggregation examples
    aggregations = {}
    aggs = ExperimentalDevice.objects.aggregate(
        avg=PintAvg("portal_diameter"),
        max=PintMax("portal_diameter"),
        min=PintMin("portal_diameter"),
        sum=PintSum("portal_diameter"),
    )

    for agg_name, value in aggs.items():
        if value is not None:
            aggregations[f'{"portal_diameter"}_{agg_name}'] = {"value": value}

    context = {
        "device": device,
        "other_device": ExperimentalDevice.objects.last(),
        "unit_choices": field.unit_choices,
        "aggregations": aggregations,
    }

    return TemplateResponse(request, template, context)
