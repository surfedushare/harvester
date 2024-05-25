import json

from django import forms


class PrettyJSONWidget(forms.Textarea):

    def format_value(self, value):
        try:
            if value:
                json_value = json.loads(value)
                return json.dumps(json_value, indent=4, sort_keys=True)
        except json.JSONDecodeError:
            return value
        return value
