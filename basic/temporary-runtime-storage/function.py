from textwrap import dedent
from samsarafntempstorage import temp_storage_path


def main(_, __):
    temp_dir = temp_storage_path()

    my_csv = temp_dir / "my.csv"

    my_csv.write_text(
        dedent("""name,age
        John,25
        Jane,30
        """)
    )

    print("Storage contents", [f.name for f in temp_dir.iterdir()])
    print("File path", str(my_csv))
