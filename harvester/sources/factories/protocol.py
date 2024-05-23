from typing import Protocol


class ResourceFactoryProtocol(Protocol):

    head: dict

    @classmethod
    def create_common_responses(cls):
        raise NotImplementedError("Missing create_common_responses implementation")

    @classmethod
    def create_delta_responses(cls):
        raise NotImplementedError("Missing create_delta_responses implementation")
