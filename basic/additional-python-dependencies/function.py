from samsarafndeps import setup_additional_dependency_path

setup_additional_dependency_path("lib")

import cowsay  # noqa: E402


def main(_, __):
    print(cowsay.get_output_string("cow", "Additional dependencies in Functions!"))
