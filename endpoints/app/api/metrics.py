from dataclasses import dataclass
from typing import List
from flask_marshmallow import Schema
from sqlalchemy import func
from datetime import datetime, timedelta
from app.api.utils import create_events_evolution_graph
from flask import send_file
from app.models import Event
from app.api import bp
from app import db
from apifairy import response, other_responses
import marshmallow_dataclass


@dataclass
class AveragePRTimeResponse:
    Time: int


@dataclass
class EventCountsResponse:
    PullRequestEvent: int
    IssuesEvent: int
    WatchEvent: int


EVENT_TYPES = ["PullRequestEvent", "IssuesEvent", "WatchEvent"]


@bp.route("/metrics/average_pr_time/<repo_name>", methods=["GET"])
@response(
    marshmallow_dataclass.class_schema(
        AveragePRTimeResponse, base_schema=Schema
    )
)
def average_pr_time(repo_name: str):
    """
    This endpoint returns the average time of pull requests for a specific repository.

    Parameters:
        - repo_name: Name of the repository.

    Returns:
        - Average time for pull requests in seconds. -1 if there is not enough data.
    """
    pr_events: List[Event] = (
        db.session.query(Event.created_at)
        .filter_by(type="PullRequestEvent", repo_name=repo_name)
        .order_by(Event.created_at)
        .all()
    )
    if len(pr_events) < 2:
        return AveragePRTimeResponse(-1)

    times = [event.created_at for event in pr_events]
    average_delta = sum(
        (times[i + 1] - times[i]).total_seconds()
        for i in range(len(times) - 1)
    ) / (len(times) - 1)

    return AveragePRTimeResponse(average_delta)


@bp.route("/metrics/event_counts/<int:offset>", methods=["GET"])
@response(
    marshmallow_dataclass.class_schema(EventCountsResponse, base_schema=Schema)
)
def event_counts(offset: int):
    """
    This endpoint returns the counts of different events happened in the past specified minutes.

    Parameters:
        - offset: The past time in minutes from the current time.

    Returns:
        - A dictionary with the counts of different events.
    """
    offset_datetime = datetime.utcnow() - timedelta(minutes=offset)
    event_counts = (
        db.session.query(Event.type, func.count(Event.type))
        .filter(Event.created_at >= offset_datetime)
        .group_by(Event.type)
        .all()
    )
    # Add 0 for missing event types
    event_counts = dict(event_counts)
    for event in EVENT_TYPES:
        if event not in event_counts:
            event_counts[event] = 0

    return EventCountsResponse(**event_counts)


@bp.route("/metrics/events_per_minute_image/<int:offset>", methods=["GET"])
@other_responses(
    {
        200: "An image file (png format) that represents the events distribution per minute."
    }
)
def event_per_minute_image(offset: int):
    """
    This endpoint returns an image showing the distribution of events per minute.

    Parameters:
        - offset: The past time in minutes from the current time.

    Returns:
        - An image file (png format) that represents the events distribution per minute.
    """
    now = datetime.utcnow()
    offset_datetime = now - timedelta(minutes=offset)
    events = (
        db.session.query(Event.type, Event.created_at)
        .filter(Event.created_at >= offset_datetime)
        .all()
    )
    buf = create_events_evolution_graph(
        events, offset_datetime, now, EVENT_TYPES
    )
    return send_file(buf, mimetype="image/png")
