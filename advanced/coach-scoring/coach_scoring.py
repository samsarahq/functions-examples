import samsara
import requests
import datetime

SAMSARA_DRIVER_SAFETY_SCORE_API_URL = "https://api.samsara.com/v1/fleet/drivers/{driverId}/safety/score?startMs={startMs}&endMs={endMs}"
SAMSARA_DRIVER_COACH_ASSIGNMENTS_API_URL = "https://api.samsara.com/coaching/driver-coach-assignments"
SAMSARA_USER_RETRIEVAL_API_URL = "https://api.samsara.com/users/{userId}"

LIMIT_N_DRIVERS_PER_COACH = 10
SCORE_PERIOD_SIZE_DAYS = 11

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"

class FunctionContext:
    def __init__(self):
        self._function = samsara.Function()
        self._secrets = self._function.secrets().load()

    def get_secrets(self):
        return self._secrets

def driver_safety_scores(context, driverId):
    TIME_NOW = datetime.datetime.now(datetime.timezone.utc)

    SCORE_PERIODS = [
        (int((TIME_NOW - datetime.timedelta(hours=24)).timestamp() * 1000), int(TIME_NOW.timestamp() * 1000)),
        (int((TIME_NOW - datetime.timedelta(days=SCORE_PERIOD_SIZE_DAYS)).timestamp() * 1000), int((TIME_NOW - datetime.timedelta(days=SCORE_PERIOD_SIZE_DAYS-1)).timestamp() * 1000)),
    ]

    SAMSARA_API_HEADERS = {
        "accept": "application/json",
        "authorization": f"Bearer {context.get_secrets()["SAMSARA_API_TOKEN"]}"
    }

    scores = []
    for startMs, endMs in SCORE_PERIODS:
        URL = SAMSARA_DRIVER_SAFETY_SCORE_API_URL.format(driverId=driverId, startMs=startMs, endMs=endMs)
        response = requests.get(URL, headers=SAMSARA_API_HEADERS)

        if response.status_code != 200:
            raise Exception(f"Failed to get driver safety score: {response.status_code} {response.text}")
    
        scores.append(int(response.json()["safetyScore"]))

    return {"previous_score": scores[0], "current_score": scores[1]}

def driver_coach_assignments(context):
    SAMSARA_API_HEADERS = {
        "accept": "application/json",
        "authorization": f"Bearer {context.get_secrets()["SAMSARA_API_TOKEN"]}"
    }

    URL = SAMSARA_DRIVER_COACH_ASSIGNMENTS_API_URL
    
    response = requests.get(URL, headers=SAMSARA_API_HEADERS)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get driver coach assignments: {response.status_code} {response.text}")
    
    response_json = response.json()
    if "data" not in response_json:
        return []
    
    assignment_pairs = []
    for assignment in response_json["data"]:
        if "driver" not in assignment:
            continue

        if "driverId" not in assignment["driver"] or "coachId" not in assignment:
            continue

        assignment_pairs.append((assignment["driver"]["driverId"], assignment["coachId"],))
    
    return assignment_pairs

def name_of_coach(context, coachId):
    SAMSARA_API_HEADERS = {
        "accept": "application/json",
        "authorization": f"Bearer {context.get_secrets()["SAMSARA_API_TOKEN"]}"
    }
    
    URL = SAMSARA_USER_RETRIEVAL_API_URL.format(userId=coachId)
    response = requests.get(URL, headers=SAMSARA_API_HEADERS)

    if response.status_code != 200:
        raise Exception(f"Failed to get coach name: {response.status_code} {response.text}")
    
    if "data" not in response.json():
        raise Exception(f"Missing data in response")
    
    if "name" not in response.json()["data"]:
        raise Exception(f"Missing name in response data")
    
    return response.json()["data"]["name"]

def main(event, context):
    context = FunctionContext()

    # A coach gets scored as follows:
    # - If 10% or more of their drivers have a safety score reduction: -1
    # - If 15% or more of their drivers have a safety score increase, and
    #   the rest of their drivers don't have a safety score reduction: +1
    # - Otherwise: 0

    SCORE_REDUCTION_THRESHOLD = 0.1
    SCORE_INCREASE_THRESHOLD = 0.15

    NOTIFY_WEBHOOK = context.get_secrets()["NOTIFY_WEBHOOK"]

    coach_assignments = driver_coach_assignments(context)
    coaches = {}

    if len(coach_assignments) == 0:
        print("No coach assignments found")
        return

    processed_coaches = set()
    num_drivers = 0
    for driverId, coachId in coach_assignments:
        if coachId in processed_coaches:
            continue

        safety_scores = driver_safety_scores(context, driverId)
        print(f"Driver {driverId} has coach {coachId} and scores: {safety_scores['previous_score']} -> {safety_scores['current_score']}")

        if coachId not in coaches:
            coaches[coachId] = {"score": 0, "total_drivers": 0, "drivers_with_score_reduction": 0, "drivers_with_score_increase": 0}

        if safety_scores["current_score"] < safety_scores["previous_score"]:
            coaches[coachId]["drivers_with_score_reduction"] += 1
        elif safety_scores["current_score"] > safety_scores["previous_score"]:
            coaches[coachId]["drivers_with_score_increase"] += 1

        coaches[coachId]["total_drivers"] += 1
        num_drivers += 1

        if num_drivers >= LIMIT_N_DRIVERS_PER_COACH:
            num_drivers = 0
            processed_coaches.add(coachId)
            print("Driver limit reached, skipping to next coach")
            continue

    all_scores_display = "Coach scores:\n\n"
    for coachId, coach in coaches.items():
        if coach["drivers_with_score_reduction"] / coach["total_drivers"] >= SCORE_REDUCTION_THRESHOLD:
            coach["score"] = -1
        elif coach["drivers_with_score_increase"] / coach["total_drivers"] >= SCORE_INCREASE_THRESHOLD and coach["drivers_with_score_reduction"] == 0:
            coach["score"] = 1

        coach_name = name_of_coach(context, coachId)
        score_display = "+1" if coach["score"] > 0 else "-1" if coach["score"] < 0 else "0"
        summary_display = f"{coach_name} (ID {coachId}) score update: {score_display}"
        print(summary_display)

        all_scores_display += f"{summary_display}\n"

    requests.post(NOTIFY_WEBHOOK, json={"message": all_scores_display})
