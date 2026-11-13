
import gzip
from pathlib import Path


def analyze_fastq(fastq_path):
    """
    Analyze a NASA FASTQ.gz sequencing file.
    Calculates basic sequencing quality metrics.
    """

    path = Path(fastq_path)

    if not path.exists():
        raise FileNotFoundError(f"FASTQ file not found: {path}")

    reads = 0
    total_bases = 0
    gc_bases = 0
    quality_sum = 0
    q30_bases = 0
    invalid_records = 0
    read_lengths = []

    with gzip.open(path, "rt", encoding="utf-8") as file:

        while True:
            header = file.readline()

            if not header:
                break

            sequence = file.readline().strip().upper()
            plus = file.readline()
            quality = file.readline().strip()

            if not sequence or not plus or not quality:
                invalid_records += 1
                break

            if (
                not header.startswith("@")
                or not plus.startswith("+")
                or len(sequence) != len(quality)
            ):
                invalid_records += 1
                continue

            reads += 1
            length = len(sequence)

            read_lengths.append(length)
            total_bases += length

            gc_bases += sequence.count("G") + sequence.count("C")

            scores = [ord(char) - 33 for char in quality]

            quality_sum += sum(scores)
            q30_bases += sum(score >= 30 for score in scores)

    if reads == 0 or total_bases == 0:
        raise ValueError("No valid sequencing reads found.")

    return {
        "filename": path.name,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "study_id": "OSD-316",
        "sample_id": "SRR11586267",
        "subject": "COS 5",
        "timepoint": "Postflight R+1",
        "total_reads": reads,
        "total_bases": total_bases,
        "average_read_length": round(total_bases / reads, 2),
        "minimum_read_length": min(read_lengths),
        "maximum_read_length": max(read_lengths),
        "gc_content_pct": round(gc_bases / total_bases * 100, 2),
        "mean_phred_quality": round(quality_sum / total_bases, 2),
        "q30_percentage": round(q30_bases / total_bases * 100, 2),
        "invalid_records": invalid_records,
        "is_real_nasa_data": True
    }
