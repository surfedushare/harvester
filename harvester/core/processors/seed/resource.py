from copy import deepcopy
from collections import OrderedDict

from datagrowth.datatypes import CollectionBase
from datagrowth.configuration import create_config, ConfigurationType
from datagrowth.resources.http.iterators import send_serie_iterator
from datagrowth.processors import Processor
from datagrowth.processors.input.iterators import content_iterator
from datagrowth.utils import ibatch


class ResourceSeedingProcessor(Processor):

    Document = None

    resource_type = None
    contribute_type = "extract_processor"

    initial = None
    contents = {}
    buffer = []
    batch = []

    def should_skip_phase(self, phase):
        if not self.contents:
            return False
        highest_content_phase = max(self.contents.keys())
        return phase["phase"].index < highest_content_phase

    def build_seed_iterator(self, phase, *args, **kwargs):
        resource_config = phase["retrieve"]
        if not len(self.batch):
            args_list = [args]
            kwargs_list = [kwargs]
        else:
            args_list = [args]
            kwargs_list = [kwargs]
        resource_iterator = send_serie_iterator(
            args_list, kwargs_list,
            method=resource_config.method,
            config=resource_config
        )
        seed_iterator = content_iterator(resource_iterator, phase["contribute"].objective)
        batch_size = phase["phase"].batch_size
        return ibatch(seed_iterator, batch_size=batch_size) if batch_size else seed_iterator

    def flush_buffer(self, phase, force=False):
        if not self.buffer and not force:
            raise ValueError(f"Did not expect to encounter an empty buffer with strategy for phase {phase['phase']}")

        match phase["phase"].strategy:
            case "initial" | "replace":
                self.batch = deepcopy(self.buffer)
            case "merge":
                raise NotImplementedError("Merge strategy not implemented")

        self.buffer = []

    def batch_to_documents(self):
        documents = [
            self.Document.build(seed)
            for seed in self.batch
        ]
        return self.collection.update_batches(documents, self.collection.identifier)

    def __init__(self, collection: CollectionBase, config: ConfigurationType | dict, initial: bool = None):
        super().__init__(config)
        assert len(self.config.phases), \
            "ResourceSeedingProcessor needs at least one phase to be able to retrieve seed data"
        assert collection.identifier, (
            "ResourceSeedingProcessor expects a Collection with the identifier set to a Document property "
            "that has a unique value across Documents in the Collection."
        )
        self.collection = collection
        self.Document = collection.get_document_model()
        self.resources = {}
        self.buffer = None  # NB: "None" ensures the forever while loop runs at least once
        self.batch = initial or []
        self.phases = OrderedDict()
        for ix, phase in enumerate(self.config.phases):
            phase = deepcopy(phase)
            phase["index"] = ix
            retrieve_data = phase.pop("retrieve_data")
            contribute_data = phase.pop("contribute_data")
            phase_config = create_config("seeding_processor", phase)
            retrieve_config = create_config(self.resource_type, retrieve_data)
            contribute_config = create_config(self.contribute_type, contribute_data)
            self.phases[phase_config.phase] = {
                "phase": phase_config,
                "retrieve": retrieve_config,
                "contribute": contribute_config
            }

    def __call__(self, *args, **kwargs):
        while self.contents or self.buffer is None:
            for phase_index, phase in enumerate(self.phases.values()):
                if self.should_skip_phase(phase):
                    continue
                match phase["phase"].strategy:
                    case "initial" | "replace":
                        if phase_index not in self.contents:
                            self.contents[phase_index] = self.build_seed_iterator(phase, *args, **kwargs)
                        try:
                            self.buffer = next(self.contents[phase_index])
                        except StopIteration:
                            # The contents iterator is exhausted.
                            # We'll flush the currently empty buffer
                            self.flush_buffer(phase, force=True)
                            # We remove the iterator from memory
                            del self.contents[phase_index]
                            # And retry phases before this phase (if any)
                            break
                    case "merge":
                        self.buffer = list(self.build_seed_iterator(phase, *args, **kwargs))
                self.flush_buffer(phase)
            if not self.batch:
                return
            for batch in self.batch_to_documents():
                yield batch


class HttpSeedingProcessor(ResourceSeedingProcessor):
    resource_type = "http_resource"
