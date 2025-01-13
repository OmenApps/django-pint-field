"""Views for managing fictional universes."""

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ..forms import UniverseForm
from ..models import Laboratory
from ..models import Universe


@login_required
def universe_list(request):
    """Display list of fictional universes."""
    template = "laboratory/universes/universe_list.html"
    context = {}
    universes = Universe.objects.all()

    # Get lab counts per universe
    lab_counts = {universe.id: Laboratory.objects.filter(universe=universe).count() for universe in universes}

    context["universes"] = universes
    context["lab_counts"] = lab_counts
    return TemplateResponse(request, template, context)


@login_required
def universe_detail(request, pk):
    """Display details of a specific universe."""
    template = "laboratory/universes/universe_detail.html"
    context = {}

    universe = get_object_or_404(Universe, pk=pk)

    # Get all labs in this universe
    labs = Laboratory.objects.filter(universe=universe)

    # Compute universe statistics
    stats = {
        "total_labs": labs.count(),
        "evil_labs": labs.filter(is_evil=True).count(),
        "avg_containment": labs.aggregate(Avg("containment_level"))["containment_level__avg"],
        "avg_stability": labs.aggregate(Avg("dimensional_stability"))["dimensional_stability__avg"],
        "high_risk_labs": labs.filter(containment_level__gte=4).count(),
    }

    context["universe"] = universe
    context["laboratories"] = labs
    context["stats"] = stats
    return TemplateResponse(request, template, context)


@login_required
def universe_create(request):
    """Create a new universe."""
    template = "laboratory/universes/universe_form.html"
    context = {}

    if request.method == "POST":
        form = UniverseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("universe_list")
    else:
        form = UniverseForm()

    context["form"] = form
    context["title"] = "Create New Universe"
    context["submit_text"] = "Create Universe"
    return TemplateResponse(request, template, context)


@login_required
def universe_update(request, pk):
    """Update an existing universe."""
    template = "laboratory/universes/universe_form.html"
    context = {}

    universe = get_object_or_404(Universe, pk=pk)

    if request.method == "POST":
        form = UniverseForm(request.POST, instance=universe)
        if form.is_valid():
            form.save()
            return redirect("universe_detail", pk=universe.pk)
    else:
        form = UniverseForm(instance=universe)

    context["form"] = form
    context["title"] = f"Update Universe: {universe.name}"
    context["submit_text"] = "Update Universe"
    context["universe"] = universe
    return TemplateResponse(request, template, context)
