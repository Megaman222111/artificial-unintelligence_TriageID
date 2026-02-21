from django.core.management.base import BaseCommand, CommandError
from pathlib import Path

from risk_scoring.train import train_and_save


class Command(BaseCommand):
    help = "Train and persist the patient risk model from CSV data."

    def add_arguments(self, parser):
        parser.add_argument("--min-rows", type=int, default=25)
        parser.add_argument("--min-positives", type=int, default=5)
        parser.add_argument(
            "--allow-low-positives",
            action="store_true",
            help="Allow training with fewer than --min-positives positive labels.",
        )
        parser.add_argument(
            "--csv-path",
            type=str,
            default="",
            help="Optional path to training CSV. Defaults to webapp/risk_scoring/data/diabetic_data.csv.",
        )
        parser.add_argument(
            "--max-rows",
            type=int,
            default=50000,
            help="Max training rows to sample from CSV (set 0 to use all rows).",
        )

    def handle(self, *args, **options):
        csv_path_raw = (options.get("csv_path") or "").strip()
        csv_path = Path(csv_path_raw).expanduser() if csv_path_raw else None
        max_rows = options.get("max_rows")
        if max_rows is not None and max_rows <= 0:
            max_rows = None

        try:
            result = train_and_save(
                min_rows=options["min_rows"],
                min_positives=options["min_positives"],
                allow_low_positives=options["allow_low_positives"],
                csv_path=csv_path,
                max_rows=max_rows,
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"trained model_version={result.model_version} rows={result.rows} "
                f"positives={result.positives} calibrator={result.calibrator} "
                f"metrics={result.metrics}"
            )
        )
