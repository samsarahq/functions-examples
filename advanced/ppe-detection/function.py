# ruff: noqa: E402
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from samsarafndeps import setup_additional_dependency_path
from samsarafnstorage import get_storage, get_database

setup_additional_dependency_path("lib")

import adapters.email
import adapters.detection
import adapters.media

from adapters.detection import DetectionResult


def main(event, _):
    trigger_source = event["SamsaraFunctionTriggerSource"]
    if trigger_source == "alert":
        vehicle_id = event["assetId"]
        alert_occured_at = datetime.fromtimestamp(
            int(event["alertIncidentTime"]) / 1000, tz=timezone.utc
        )

        request_image_retrieval(vehicle_id, alert_occured_at)
        return

    if trigger_source == "schedule":
        to_email = event["ToEmail"]

        download_images()
        analyze_images()
        notify_about_offenders(to_email)
        return
    
    print(f"Trigger source {trigger_source} is not supported in this Function, skipping execution")


db_retrievals = get_database("ppe/retrievals")


def request_image_retrieval(vehicle_id: str, moment: datetime):
    retrieval_id = adapters.media.start_road_facing_image_retrieval(vehicle_id, moment)

    if retrieval_id is None:
        print(
            f"Retrieval impossible for {vehicle_id} at {moment.isoformat()}, skipping"
        )
        return

    db_retrievals.put_dict(
        retrieval_id,
        {
            "vehicle_id": vehicle_id,
            "requested_for": moment.isoformat(),
            "requested_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    print(f"Requested retrieval for {vehicle_id} at {moment.isoformat()}")


@dataclass
class AnalysisResult:
    image_key: str
    detection: DetectionResult = None


db_downloaded = get_database("ppe/downloaded")


def download_images():
    storage = get_storage()

    for retrieval_id in db_retrievals.keys():
        image_bytes = adapters.media.get_available_retrieval_image(retrieval_id)
        if image_bytes is None:
            print(f"Retrieval {retrieval_id} not ready yet")
            continue

        results = AnalysisResult(image_key=f"ppe/media/{retrieval_id}.jpg")
        storage.put(results.image_key, image_bytes)

        db_retrievals.delete(retrieval_id)
        db_downloaded.put_dict(retrieval_id, asdict(results))
        print(f"Retrieval {retrieval_id} downloaded")

    else:
        print("No retrievals to poll for")


db_analyzed = get_database("ppe/analyzed")


def analyze_images():
    storage = get_storage()

    for retrieval_id in db_downloaded.keys():
        results = AnalysisResult(**db_downloaded.get_dict(retrieval_id))

        results.detection = adapters.detection.detect_missing_ppe(
            storage.get_body_base64(results.image_key)
        )

        db_downloaded.delete(retrieval_id)
        db_analyzed.put_dict(retrieval_id, asdict(results))
        print(f"Analyzed {retrieval_id} with result {results.detection}")

    else:
        print("No pending images to analyze")


db_notified = get_database("ppe/notified")


def notify_about_offenders(to_email: str):
    storage = get_storage()

    for retrieval_id in db_analyzed.keys():
        analyzed = db_analyzed.get_dict(retrieval_id)
        result = AnalysisResult(**analyzed)
        result.detection = DetectionResult(**analyzed["detection"])

        if not result.detection.is_any_ppe_missing:
            print(f"No PPE missing for {retrieval_id}", result.detection)
            db_analyzed.delete(retrieval_id)
            storage.delete(result.image_key)
            continue

        attachments = [(f"{retrieval_id}.jpg", storage.get_body(result.image_key))]

        adapters.email.send(
            to_email,
            "Personnel without Protective Equipment was detected",
            attachments,
            adapters.email.Variables(
                NotificationTitle="Personnel without Protective Equipment was detected",
                NotificationSubtitle="See related image in the attachment.",
                DevNotificationMainContent=result.detection.summary,
            ),
        )

        db_analyzed.delete(retrieval_id)
        db_notified.put_dict(retrieval_id, asdict(result))

        print(
            f"Notified about offending {retrieval_id} image with result {result.detection}"
        )

    else:
        print("No offending images to notify about")
