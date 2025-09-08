import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class SamsaraRegion:
    region: Literal["us", "eu", "ca"]

    def to_api_url(self) -> str:
        prefix = f".{self.region}" if self.region != "us" else ""

        return f"https://api{prefix}.samsara.com"

    def select(self, *, us=None, eu=None, ca=None):
        if self.region == "eu":
            return eu
        elif self.region == "ca":
            return ca

        return us


default = SamsaraRegion(region="us")
valid_regions = ["us", "eu", "ca"]


def get_region() -> SamsaraRegion:
    region = os.environ.get("AWS_DEFAULT_REGION")
    if region is None:
        return default

    parts = region.split("-")
    if len(parts) != 3:
        return default

    region = parts[0]
    if region not in valid_regions:
        return default

    return SamsaraRegion(region=region)
