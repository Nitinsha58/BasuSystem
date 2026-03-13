from __future__ import annotations

from datetime import date
from typing import Optional

from registration.models import AcademicSession


def _choose_nearest_by_date(target: date, sessions: list[AcademicSession]) -> Optional[AcademicSession]:
    if not sessions:
        return None

    # Within an existing session range (inclusive)
    for session in sessions:
        if session.start_date and session.end_date and session.start_date <= target <= session.end_date:
            return session

    # Before the first session => pick the first upcoming session
    first = sessions[0]
    if first.start_date and target < first.start_date:
        return first

    # Between sessions (gaps) => pick the next upcoming session
    for prev_session, next_session in zip(sessions, sessions[1:]):
        if (
            prev_session.end_date
            and next_session.start_date
            and prev_session.end_date < target < next_session.start_date
        ):
            return next_session

    # After the last known session => pick the last session
    return sessions[-1]


def select_session_for_date(target: date) -> Optional[AcademicSession]:
    """Select an AcademicSession for an inquiry created on `target`.

    Priority:
    1) Sessions whose start_date.year == target.year (nearest/upcoming rules)
    2) Active session
    3) Nearest session overall (nearest/upcoming rules)

    Returns None only if there are no sessions at all.
    """

    sessions = list(AcademicSession.objects.all().order_by('start_date'))
    if not sessions:
        return None

    year_sessions = [s for s in sessions if s.start_date and s.start_date.year == target.year]
    if year_sessions:
        chosen = _choose_nearest_by_date(target, year_sessions)
        if chosen:
            return chosen

    active = AcademicSession.get_active()
    if active:
        return active

    return _choose_nearest_by_date(target, sessions)
