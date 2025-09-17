from samsarafnsecrets import get_secrets


def main(_, __):
    secrets = get_secrets()
    print({"secretsCount": len(secrets)})
