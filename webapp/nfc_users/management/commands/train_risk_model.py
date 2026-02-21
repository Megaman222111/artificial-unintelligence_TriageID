from django.core.management.base import BaseCommand, CommandError

from risk_scoring.train import train_and_save


class Command(BaseCommand):
    help = "Train and persist the patient 30-day deterioration risk model."

    def add_arguments(self, parser):
        parser.add_argument("--min-rows", type=int, default=25)
        parser.add_argument("--min-positives", type=int, default=5)
        parser.add_argument(
            "--allow-low-positives",
            action="store_true",
            help="Allow training with fewer than --min-positives real positive labels.",
        )

    def handle(self, *args, **options):
        try:
            result = train_and_save(
                min_rows=options["min_rows"],
                min_positives=options["min_positives"],
                allow_low_positives=options["allow_low_positives"],
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
