from typing import List
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils import create_events_evolution_graph
from flask import jsonify, send_file
from app.models import Event
from app.api import bp
from app.api.errors import bad_request, error_response, info_response



@bp.route("/metrics/average_pr_time/<repo_name>", methods=['GET'])
def average_pr_time(repo_name: str):
    pr_events: List[Event] = (
        Event.query
        .filter_by(type="PullRequestEvent", repo_name=repo_name)
        .order_by(Event.created_at).all()
    )
    if len(pr_events) < 2:
        return info_response('Not enough data to compute average PR time'), 204

    times = [event.created_at for event in pr_events]
    average_delta = sum(
        (times[i + 1] - times[i]).total_seconds()
        for i in range(len(times) - 1)
    ) / (len(times) - 1)

    return jsonify({
        'average_pr_time': int(average_delta)
    })


@bp.route("/metrics/event_counts/<int:offset>")
def event_counts(offset: int):
    offset_datetime = datetime.utcnow() - timedelta(minutes=offset)
    event_counts = (
        db_session.query(func.count(Event.type))
        .filter(Event.created_at >= offset_datetime)
        .group_by(Event.type)
        .all()
    )
    return dict(event_counts)



@bp.route('/metrics/event_per_minute_image/<int:offset>')
def event_per_minute_image(offset: int):
    now = datetime.utcnow()
    offset_datetime = now - timedelta(minutes=offset)
    events = db_session.query(Event.type, Event.created_at).filter(Event.created_at >= offset_datetime).all()
    if len(events) == 0:
        return '', 204

    buf = create_events_evolution_graph(events, offset_datetime, now)

    # Save it to a BytesIO object
    return send_file(buf, mimetype='image/png')