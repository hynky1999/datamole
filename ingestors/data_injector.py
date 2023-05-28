import json
import os
from typing import Any, Callable, List
from dataclasses import dataclass
from itertools import takewhile
from datetime import datetime, timedelta

from kafka import KafkaProducer
from models import Event
import logging
import requests
import time
import re
import config


@dataclass
class RetrievalResult:
    events: List[Event]
    etag: str | None
    poll_interval: int | None
    max_page: int | None


# Would have to spend more time to get typing right
def iterval_decorator(default_interval: int):
    def decorator(
        fetch_function: Callable[..., RetrievalResult]
    ) -> Callable[..., RetrievalResult]:
        # Decorator that will respect
        interval: int = default_interval
        last_fetch_time = datetime.utcnow() - timedelta(seconds=interval)

        def fetch_intervaled(*args: Any):
            nonlocal last_fetch_time
            nonlocal interval
            # sleep until the next interval
            time_to_sleep = (
                last_fetch_time
                + timedelta(seconds=interval)
                - datetime.utcnow()
            ).total_seconds()
            time.sleep(max(time_to_sleep, 0))
            result = None
            try:
                result = fetch_function(*args)
                # 0 for interval doesn't make sense anyway
                interval = result.poll_interval or interval
            finally:
                last_fetch_time = datetime.utcnow()
            return result

        return fetch_intervaled

    return decorator


def get_max_page(link: str):
    last_link_re = re.compile(
        r'<https://api.github.com/events\?page=(\d+)[^>]*>; rel="last"',
        re.IGNORECASE,
    )
    search_result = last_link_re.search(link)
    if not search_result:
        return None
    return int(search_result.group(1))


@iterval_decorator(60)
def request_github_events(page: int, etag: str | None):
    headers = {}
    if etag is not None:
        headers["If-None-Match"] = etag

    url = f"https://api.github.com/events?page={page}&per_page=100"
    logging.debug(f"Fetching {url} with headers {headers}")
    response = requests.get(url, headers=headers)
    if response.status_code == 304:
        # No new events
        return RetrievalResult([], etag, None, None)

    if response.status_code != 200:
        raise ValueError(
            f"Got status code {response.status_code} with body {response.text}"
        )

    etag = response.headers["ETag"] if "ETag" in response.headers else None
    poll_interval = (
        int(response.headers["X-Poll-Interval"])
        if "X-Poll-Interval" in response.headers
        else None
    )
    # If we didn't find a max page, we are on the last page
    max_page = get_max_page(response.headers["Link"]) or page
    logging.debug(
        f"Got response {response.status_code} with etag {etag} and poll interval {poll_interval} and max page {max_page}"
    )
    events: List[Event] = []
    for event in response.json():
        if event["type"] in ["WatchEvent", "PullRequestEvent", "IssuesEvent"]:
            db_event = Event(
                id=int(event["id"]),
                type=event["type"],
                repo_name=event["repo"]["name"],
                created_at=datetime.strptime(
                    event["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                ),
            )
            events.append(db_event)

    return RetrievalResult(events, etag, poll_interval, max_page)


def push_events_to_queue(kafka_producer: KafkaProducer, events: List[Event]):
    for event in events:
        # convert to bytes
        message = json.dumps(event.to_dict()).encode("utf-8")
        kafka_producer.send(config.KAFKA_TOPIC, message)


def get_new_events(
    last_event_id: int | None, etag: str | None, traverse_pages: bool = True
):
    page = 1
    events: List[Event] = []
    # Dummy response
    response = RetrievalResult([], etag, 30, None)
    while (
        response.max_page is None
        or page <= response.max_page
        and page == 1
        or traverse_pages
    ):
        # Send it with last etag
        try:
            response = request_github_events(page, response.etag)
        except ValueError as e:
            logging.error(f"Error fetching events: {e}")
            break

        new_events = (
            list(
                takewhile(
                    lambda event: event.id != last_event_id, response.events
                )
            )
            if last_event_id is not None
            else response.events
        )
        events.extend(new_events)
        if len(new_events) < len(response.events):
            # we have found the last event
            break
        else:
            page += 1

    newest_event_id: int | None = events[0].id if len(events) > 0 else None
    # Due to page traversal, we may have duplicates
    events = list(set(events))
    return (
        RetrievalResult(
            events, response.etag, response.poll_interval, response.max_page
        ),
        newest_event_id,
    )


def fetch_and_process_gh_events(kafka_producer: KafkaProducer):
    last_id: int | None = None
    etag: str | None = None
    while True:
        response, last_id = get_new_events(last_id, etag, traverse_pages=False)
        push_events_to_queue(kafka_producer, response.events)
        etag = response.etag
        logging.info(f"Fetched {len(response.events)} events")


def init_kafka():
    while True:
        try:
            kafka_producer = KafkaProducer(bootstrap_servers=config.KAFKA_URL)
            break
        except Exception as e:
            logging.error(f"Error connecting to kafka: {e}")
            time.sleep(5)
    return kafka_producer


def main():
    kafka_producer = init_kafka()
    fetch_and_process_gh_events(kafka_producer)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
    main()
