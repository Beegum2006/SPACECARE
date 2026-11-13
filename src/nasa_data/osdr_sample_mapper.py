import zipfile
import csv
from pathlib import Path


def load_osdr_sample_metadata(zip_path):
    """
    Read sample metadata from an OSDR ISA metadata ZIP.
    Returns sample-level metadata as a list of dictionaries.
    """

    zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"Metadata ZIP not found: {zip_path}")

    samples = []

    with zipfile.ZipFile(zip_path, "r") as archive:

        sample_files = [
            name for name in archive.namelist()
            if name.startswith("s_") and name.endswith(".txt")
        ]

        if not sample_files:
            raise ValueError("No sample metadata file found in ZIP.")

        for filename in sample_files:
            with archive.open(filename) as file:
                text = file.read().decode("utf-8-sig").splitlines()

            reader = csv.DictReader(text, delimiter="\t")

            for row in reader:
                clean_row = {
                    key.strip(): value.strip() if value else ""
                    for key, value in row.items()
                    if key
                }

                samples.append(clean_row)

    return samples
def create_sample_catalogue(records):
    """Convert raw OSDR metadata into a clean sample catalogue."""

    catalogue = []

    for row in records:
        catalogue.append({
            "sample_id": row.get("Sample Name", ""),
            "source_name": row.get("Source Name", ""),
            "subject": row.get("Factor Value[Study Subject]", ""),
            "group": row.get("Factor Value[Spaceflight]", ""),
            "timepoint": row.get("Factor Value[Time]", ""),
            "sex": row.get("Characteristics[sex]", ""),
            "organism": row.get("Characteristics[Organism]", ""),
            "material": row.get("Characteristics[Material Type]", "")
        })

    return catalogue
def save_sample_catalogue(catalogue, output_path):
    """Save the sample catalogue as a CSV file."""

    if not catalogue:
        raise ValueError("No sample records to save.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=catalogue[0].keys()
        )
        writer.writeheader()
        writer.writerows(catalogue)

    print(f"\nSample catalogue saved to: {output_path}")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]

    metadata_zip = (
        project_root
        / "data"
        / "nasa_downloads"
        / "OSD-316"
        / "OSD-316_metadata_GLDS-316-ISA.zip"
    )

    records = load_osdr_sample_metadata(metadata_zip)
    catalogue = create_sample_catalogue(records)
    output_csv = (
        project_root
        / "data"
        / "nasa_downloads"
        / "OSD-316"
        / "osd316_sample_catalogue.csv"
    )

    save_sample_catalogue(catalogue, output_csv)

    print(f"\nTotal samples: {len(catalogue)}")
    print("\nCOMPLETE SAMPLE CATALOGUE\n")

    for sample in catalogue:
        print(
            f"{sample['sample_id']} | "
            f"{sample['subject']} | "
            f"{sample['group']} | "
            f"{sample['timepoint']}"
        )

    print("\nGROUP DISTRIBUTION")

    groups = {}

    for sample in catalogue:
        group = sample["group"]
        groups[group] = groups.get(group, 0) + 1

    for group, count in groups.items():
        print(f"{group}: {count}")

    print("\nTIMEPOINT DISTRIBUTION")

    timepoints = {}

    for sample in catalogue:
        time = sample["timepoint"]
        timepoints[time] = timepoints.get(time, 0) + 1

    for time, count in timepoints.items():
        print(f"{time}: {count}")

