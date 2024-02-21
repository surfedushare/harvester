from sources.utils.base import BaseExtractor


class PublinovaExtractor(BaseExtractor):

    @classmethod
    def webhook_data_transformer(cls, webhook_data: dict, set_name: str):
        # This method returns webhook data as if that data is coming from an API call.
        # This allows us to re-use some components and keep things DRYer.
        return {
            "data": [
                webhook_data
            ]
        }
