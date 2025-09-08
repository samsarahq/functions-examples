from samsarafnregion import get_region


def main(_, __):
    region = get_region()
    print(
        {
            "region": region.region,
            "api_url": region.to_api_url(),
            "selected": region.select(eu=1, us=2),
        }
    )
