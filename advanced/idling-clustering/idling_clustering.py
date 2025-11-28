import requests
import datetime
from urllib.parse import quote
import samsara
from geopy import distance
import time
import json

SAMSARA_IDLING_API_URL = (
    "https://api.samsara.com/fleet/reports/vehicle/idling?limit=512"
)
NUM_HOURS_HISTORY = 8
CLUSTER_DISTANCE_THRESHOLD_MILES = 2
MAX_CLUSTERS = 1000


def idling_time_buckets():
    timestamps = []

    range_start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=NUM_HOURS_HISTORY
    )

    for hour in range(NUM_HOURS_HISTORY):
        current_hours_start = range_start + datetime.timedelta(hours=hour)
        current_hours_end = current_hours_start + datetime.timedelta(hours=1)
        timestamps.append(
            (
                current_hours_start.isoformat(),
                current_hours_end.isoformat(),
            )
        )

    return timestamps


def idling_url_with_time_range(start_timestamp, end_timestamp, cursor=None):
    escaped_start_timestamp = quote(start_timestamp)
    escaped_end_timestamp = quote(end_timestamp)

    url_root = SAMSARA_IDLING_API_URL

    if cursor:
        escaped_cursor = quote(cursor)
        url_root = f"{url_root}&after={escaped_cursor}"

    return f"{url_root}&startTime={escaped_start_timestamp}&endTime={escaped_end_timestamp}"


def cursor_from_response_data(idling_reports):
    if "pagination" in idling_reports:
        if "endCursor" in idling_reports["pagination"]:
            if "hasNextPage" in idling_reports["pagination"]:
                if idling_reports["pagination"]["hasNextPage"]:
                    return idling_reports["pagination"]["endCursor"]
    return None


def idling_by_vehicle(idling_reports):
    idling_by_vehicle = {}
    for report in idling_reports:
        vehicle_name = report["vehicle"]["name"]
        vehicle_lat = report["address"]["latitude"]
        vehicle_lon = report["address"]["longitude"]

        if vehicle_name not in idling_by_vehicle:
            idling_by_vehicle[vehicle_name] = [
                (
                    vehicle_lat,
                    vehicle_lon,
                ),
            ]
        else:
            idling_by_vehicle[vehicle_name].append(
                (
                    vehicle_lat,
                    vehicle_lon,
                )
            )

    return idling_by_vehicle


def idling_clusters(idling_by_vehicle):
    potential_clusters = {}

    for vehicle_name, idle_locations in idling_by_vehicle.items():
        for idle_location in idle_locations:
            if idle_location not in potential_clusters:
                potential_clusters[idle_location] = {}

            if vehicle_name not in potential_clusters[idle_location]:
                potential_clusters[idle_location][vehicle_name] = 1
            else:
                potential_clusters[idle_location][vehicle_name] += 1

    print(potential_clusters)

    clusters = []
    starting_index = 0
    locations_in_cluster = set()

    total_clusters = len(potential_clusters)
    if total_clusters > MAX_CLUSTERS:
        print(
            f"Found {len(potential_clusters)} potential clusters, truncating to {MAX_CLUSTERS}"
        )
        potential_clusters = dict(list(potential_clusters.items())[:MAX_CLUSTERS])
        total_clusters = MAX_CLUSTERS

    processed_clusters = 0

    for idle_location, vehicle_to_event_count in potential_clusters.items():
        try:
            next_cluster_vehicle_location_histograms = vehicle_to_event_count
            other_index = 0
            for (
                other_idle_location,
                other_vehicle_to_event_count,
            ) in potential_clusters.items():
                try:
                    if other_index == starting_index:
                        continue

                    if other_idle_location in locations_in_cluster:
                        continue

                    if (
                        distance.distance(idle_location, other_idle_location).miles
                        <= CLUSTER_DISTANCE_THRESHOLD_MILES
                    ):
                        print(
                            f"Locations in range: {idle_location} and {other_idle_location}"
                        )

                        for (
                            vehicle_name,
                            event_count,
                        ) in other_vehicle_to_event_count.items():
                            if (
                                vehicle_name
                                not in next_cluster_vehicle_location_histograms
                            ):
                                next_cluster_vehicle_location_histograms[
                                    vehicle_name
                                ] = 0

                            next_cluster_vehicle_location_histograms[vehicle_name] += (
                                event_count
                            )

                        locations_in_cluster.add(idle_location)
                        locations_in_cluster.add(other_idle_location)
                finally:
                    other_index += 1
            if len(next_cluster_vehicle_location_histograms) > 0:
                clusters.append(
                    {
                        "location": idle_location,
                        "vehicles": next_cluster_vehicle_location_histograms,
                    }
                )
        finally:
            starting_index += 1

            processed_clusters += 1
            progress_float = float((processed_clusters / total_clusters) * 100)
            print(f"Progress: {progress_float:.1f}%")

    clusters = sorted(clusters, key=lambda x: sum(x["vehicles"].values()), reverse=True)

    return [cluster for cluster in clusters if sum(cluster["vehicles"].values()) >= 1]


def main(event, context):
    function = samsara.Function()
    secrets = function.secrets().load()

    SAMSARA_API_HEADERS = {
        "accept": "application/json",
        "authorization": f"Bearer {secrets['SAMSARA_API_TOKEN']}",
    }

    NOTIFY_WEBHOOK = secrets["NOTIFY_WEBHOOK"]

    time_buckets = idling_time_buckets()
    idling_reports = []
    for bucket in time_buckets:
        print(f"Querying for range {bucket[0]} to {bucket[1]}")

        cursor = None

        while True:
            response = requests.get(
                idling_url_with_time_range(bucket[0], bucket[1], cursor),
                headers=SAMSARA_API_HEADERS,
            )

            if response.status_code != 200:
                print(f"Error: {response.status_code} {response.text}")
                break

            # Rate limit requests to 10/sec, well within the API limit of 25/sec
            time.sleep(0.1)

            response_data = json.loads(response.text)
            if "data" in response_data:
                idling_reports.extend(response_data["data"])

            cursor = cursor_from_response_data(response_data)

            if not cursor:
                break

    print(f"Found {len(idling_reports)} idling report(s)")
    for report in idling_reports:
        print(
            f"{report['vehicle']['name']} ({report['address']['latitude']}, {report['address']['longitude']})"
        )

    idle_events = idling_by_vehicle(idling_reports)
    print(idle_events)

    clusters = idling_clusters(idle_events)
    print(clusters)

    top_5_clusters = clusters[:5]
    cluster_display = "Top 5 idling clusters:\n\n"
    for index, cluster in enumerate(top_5_clusters):
        cluster_display += f"{index + 1}. {cluster['location']}: {sum(cluster['vehicles'].values())} event(s) across {len(cluster['vehicles'])} vehicle(s)\n"

    print(cluster_display)
    requests.post(NOTIFY_WEBHOOK, json={"message": cluster_display})
