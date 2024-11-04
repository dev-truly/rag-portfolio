import os

from langchain_loader.context_management.context_updater import ContextUpdater
import copy

from personaai_default import get_logger
from personaai_default.lib import get_cleaned_text

log = get_logger()
class ChromadbContextUpdater(ContextUpdater):
    def __init__(self, search_client, search_document_list):
        super().__init__(search_client, search_document_list)

    def set_contextual_chunks(self, context_size=700):
        pass

    def set_contextual_pages(self):
        pass