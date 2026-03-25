from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncMonth

from .models import Inquiry


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def get_filtered_queryset(params):
    """
    Apply optional filters (from request.GET) to the Inquiry queryset.
    All filters are optional — unset means no constraint applied.
    """
    qs = Inquiry.objects.select_related(
        "current_status",
        "campaign",
        "referral_source",
        "caller",
        "assigned_counsellor",
        "session",
        "sales_person",
    )

    session_id      = params.get("session")
    campaign_id     = params.get("campaign")
    counsellor_id   = params.get("counsellor")
    origin          = params.get("origin")
    quality         = params.get("quality")
    date_from       = params.get("date_from")
    date_to         = params.get("date_to")
    sales_person_id = params.get("sales_person")
    caller_id       = params.get("caller")

    if session_id:
        qs = qs.filter(session_id=session_id)
    if campaign_id:
        qs = qs.filter(campaign_id=campaign_id)
    if counsellor_id:
        qs = qs.filter(assigned_counsellor_id=counsellor_id)
    if origin:
        qs = qs.filter(inquiry_origin=origin)
    if quality:
        qs = qs.filter(lead_quality=quality)
    if date_from:
        try:
            from datetime import date as _date
            qs = qs.filter(created_at__date__gte=_date.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import date as _date
            qs = qs.filter(created_at__date__lte=_date.fromisoformat(date_to))
        except ValueError:
            pass
    if sales_person_id:
        qs = qs.filter(sales_person_id=sales_person_id)
    if caller_id:
        qs = qs.filter(caller_id=caller_id)

    return qs


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

CLOSED_STATUS = "closed"   # FollowUpStatus.name for converted/enrolled leads


def kpi_summary(qs):
    total    = qs.count()
    closed   = qs.filter(current_status__name__iexact=CLOSED_STATUS).count()
    hot      = qs.filter(lead_quality="hot").count()
    fake     = qs.filter(Q(lead_type="Fake")).count()

    avg_fu = (
        qs.annotate(fu_count=Count("followup"))
          .aggregate(avg=Avg("fu_count"))["avg"]
    )

    return {
        "total":        total,
        "closed":       closed,
        "hot":          hot,
        "fake":         fake,
        "avg_followups": round(float(avg_fu or 0), 1),
    }


def pipeline_breakdown(qs):
    """Count of inquiries grouped by current_status, ordered by pipeline stage."""
    rows = (
        qs.values(
            "current_status__name",
            "current_status__color",
            "current_status__order",
        )
        .annotate(count=Count("id"))
        .order_by("current_status__order")
    )
    return [
        {
            "name":  r["current_status__name"] or "No Status",
            "color": r["current_status__color"] or "#94a3b8",
            "count": r["count"],
        }
        for r in rows
    ]


def referral_source_breakdown(qs):
    """Count grouped by referral_source category + individual source name (excludes nulls)."""
    from collections import defaultdict
    rows = (
        qs.exclude(referral_source__isnull=True)
          .values("referral_source__category", "referral_source__name")
          .annotate(count=Count("id"))
          .order_by("referral_source__category", "-count")
    )
    label_map = {
        "digital":        "Digital",
        "offline":        "Offline",
        "word_of_mouth":  "Word of Mouth",
        "representative": "Representative",
    }
    cats = defaultdict(lambda: {"children": [], "total": 0})
    for r in rows:
        cat = r["referral_source__category"]
        cats[cat]["children"].append({"name": r["referral_source__name"], "value": r["count"]})
        cats[cat]["total"] += r["count"]
    return [
        {
            "category": cat,
            "label":    label_map.get(cat, cat),
            "total":    data["total"],
            "children": data["children"],
        }
        for cat, data in cats.items()
    ]


def counsellor_performance(qs):
    """Per assigned_counsellor: total leads, closed count, hot count, conversion %."""
    rows = (
        qs.exclude(assigned_counsellor__isnull=True)
          .values(
              "assigned_counsellor__id",
              "assigned_counsellor__user__first_name",
              "assigned_counsellor__user__last_name",
          )
          .annotate(
              total=Count("id"),
              closed=Count("id", filter=Q(current_status__name__iexact=CLOSED_STATUS)),
              hot=Count("id", filter=Q(lead_quality="hot")),
          )
          .order_by("-closed")
    )

    result = []
    for r in rows:
        first = r["assigned_counsellor__user__first_name"] or ""
        last  = r["assigned_counsellor__user__last_name"] or ""
        name  = f"{first} {last}".strip() or "Unknown"
        total  = r["total"]
        closed = r["closed"]
        result.append({
            "name":     name,
            "total":    total,
            "closed":   closed,
            "hot":      r["hot"],
            "conv_pct": round(closed / total * 100) if total else 0,
        })
    return result


def caller_quality(qs):
    """Per caller: calls taken, hot count, hot rate."""
    rows = (
        qs.exclude(caller__isnull=True)
          .values(
              "caller__id",
              "caller__user__first_name",
              "caller__user__last_name",
          )
          .annotate(
              calls=Count("id"),
              hot=Count("id", filter=Q(lead_quality="hot")),
          )
          .order_by("-calls")
    )

    result = []
    for r in rows:
        first = r["caller__user__first_name"] or ""
        last  = r["caller__user__last_name"] or ""
        name  = f"{first} {last}".strip() or "Unknown"
        calls = r["calls"]
        hot   = r["hot"]
        result.append({
            "name":    name,
            "calls":   calls,
            "hot":     hot,
            "hot_pct": round(hot / calls * 100) if calls else 0,
        })
    return result


def campaign_conversion(qs):
    """Per campaign: leads received, closed count, conversion %."""
    rows = (
        qs.exclude(campaign__isnull=True)
          .values("campaign__name", "campaign__id")
          .annotate(
              total=Count("id"),
              closed=Count("id", filter=Q(current_status__name__iexact=CLOSED_STATUS)),
          )
          .order_by("-total")
    )
    return [
        {
            "name":     r["campaign__name"],
            "total":    r["total"],
            "closed":   r["closed"],
            "conv_pct": round(r["closed"] / r["total"] * 100) if r["total"] else 0,
        }
        for r in rows
    ]


def origin_breakdown(qs):
    """Walk-In vs Organic Call vs Campaign: totals and closed counts."""
    rows = (
        qs.values("inquiry_origin")
          .annotate(
              total=Count("id"),
              closed=Count("id", filter=Q(current_status__name__iexact=CLOSED_STATUS)),
          )
    )
    label_map = {
        "walk_in":      "Walk-In",
        "organic_call": "Organic Call",
        "campaign":     "Campaign",
    }
    return [
        {
            "origin": label_map.get(r["inquiry_origin"], r["inquiry_origin"]),
            "total":  r["total"],
            "closed": r["closed"],
        }
        for r in rows
    ]


def quality_by_month(qs):
    """Monthly stacked breakdown of Hot / Warm / Cold leads by created_at month."""
    rows = (
        qs.annotate(month=TruncMonth("created_at"))
          .values("month", "lead_quality")
          .annotate(count=Count("id"))
          .order_by("month")
    )

    buckets = {}
    for r in rows:
        if r["month"] is None:
            continue
        key = r["month"].strftime("%b %Y")
        quality = r["lead_quality"] or "unset"
        entry = buckets.setdefault(key, {"month": key, "hot": 0, "warm": 0, "cold": 0})
        if quality == "hot":
            entry["hot"] += r["count"]
        elif quality == "warm":
            entry["warm"] += r["count"]
        elif quality == "cold":
            entry["cold"] += r["count"]

    return list(buckets.values())
