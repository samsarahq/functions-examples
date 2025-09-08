import steps.downloadretrieval
import steps.startretrieval
import steps.makepreview


def main(event, _):
    trigger_source = event["SamsaraFunctionTriggerSource"]

    if trigger_source == "alert":
        steps.startretrieval.handle(event)
        return

    if trigger_source == "schedule":
        steps.downloadretrieval.handle(event)
        steps.makepreview.handle(event)
        return
