from samsarafnsecrets import get_secrets, apply_to_env
import os


def main(_, __):
    secrets = get_secrets()
    print({"secretsCount": len(secrets)})

    key = list(secrets.keys())[0]
    apply_to_env(secrets)
    print(f"Secret {key} in the environment?: {key in os.environ}")
