import json

from django.core.management.base import BaseCommand

from datagrowth.configuration.serializers import DecodeConfigAction

from system_configuration.aws import ENVIRONMENT_NAMES_TO_CODES
from metadata.utils.analyse import MetadataValueComparer


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-r', '--reference', type=str, choices=list(ENVIRONMENT_NAMES_TO_CODES.keys()),
                            help="Environment code for the ground truth of the metadata value counts.")
        parser.add_argument('-p', '--peer', type=str, choices=list(ENVIRONMENT_NAMES_TO_CODES.keys()),
                            help="Environment to compare the reference environment to.")
        parser.add_argument('-f', '--fields', type=str, nargs="*",
                            help="MetadataField names to include in the comparison.")
        parser.add_argument('-c', '--cut-off', type=int, default=0,
                            help="Minimal required difference between values to include them in the output.")
        parser.add_argument('-l', '--limit', type=int, default=None,
                            help="Amount of MetadataValues to report on.")
        parser.add_argument('-vf', '--value-filters', type=str, action=DecodeConfigAction, nargs="?", default={},
                            help="Search filters to apply. In the format: field_name=value1,value2&...")

    @staticmethod
    def parse_filters(raw_filters):
        if not raw_filters:
            return
        return [
            {
                "external_id": key,
                "items": value.split(",")
            }
            for key, value in raw_filters.items()
        ]

    def handle(self, *args, **options):
        value_filters = self.parse_filters(options["value_filters"])
        comparer = MetadataValueComparer(options["reference"], options["peer"])
        comparison = comparer.compare(
            fields=options["fields"],
            cut_off=options["cut_off"],
            limit=options["limit"],
            value_filters=value_filters
        )
        self.stdout.write(json.dumps(comparison, indent=4))
