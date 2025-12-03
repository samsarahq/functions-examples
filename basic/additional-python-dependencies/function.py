import samsarafndeps  # noqa pyright: ignore[reportUnusedImport] autoload vendored packages
import cowsay


def main(_params, _context):
    print(cowsay.get_output_string("cow", "Additional dependencies in Functions!"))
