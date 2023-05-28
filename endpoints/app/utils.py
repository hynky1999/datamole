from datetime import datetime, timedelta
from io import BytesIO
from typing import List
import logging
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from app.models import Event


def create_events_evolution_graph(events: List[Event], start_date: datetime, end_date: datetime, event_types: List[str] = ['PullRequestEvent', 'IssuesEvent', 'WatchEvent']
                                  ):
    """
    Create a graph showing the evolution of events over time, and return it as a BytesIO object.
    The Events must be in range [start_date, end_date], otherwise will be ignored. If type is not in event_types, it Key error will be raised.
    :param events: List of events
    :param start_date: Start date of the graph
    :param end_date: End date of the graph
    """
    
    start_date  = start_date.replace(second=0, microsecond=0)
    end_date  = datetime.utcnow().replace(second=0, microsecond=0)
    event_counts = {
        start_date + timedelta(minutes=i): {event_type: 0 for event_type in event_types}
        for i in range(int((end_date - start_date).total_seconds() / 60))
    }
    for event in events:
        event_date = event.created_at.replace(second=0, microsecond=0)
        if event_date in event_counts:
            event_counts[event.created_at.replace(second=0, microsecond=0)][event.type] += 1
        else:
            logging.warning(f"Event {event.id} is not in range [{start_date}, {end_date}]")
        

    # Create the plot
    _, ax = plt.subplots()
    for event_type in event_types:
        dates = [date for date in event_counts.keys()]
        counts = [data[event_type] for data in event_counts.values()]
        ax.plot_date(dates, counts, '-o', label=event_type)
    ax.legend()
    plt.xticks(rotation=45)
    time_format = DateFormatter('%H:%M')  
    ax.xaxis.set_major_formatter(time_format)
    ax.set_xlabel('Time')
    ax.set_ylabel('Event count')
    ax.set_title('Events per minute')
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return buf
