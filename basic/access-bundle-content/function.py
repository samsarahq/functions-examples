from samsarafnbundle import bundle_path


def main(_, __):
    bundle = bundle_path()

    ls = sorted([f.name for f in bundle.iterdir()])
    print(f"{ls=}")

    content = (bundle / "samsarafnbundle.py").read_text()
    print("\n", content)
