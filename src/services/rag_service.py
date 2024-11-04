import os
import re
from concurrent import futures

from langchain_loader import query_documents_from_collection
from langchain_loader.embeddings import get_embedding
from proto.py import Rag_stub, Rag_c
from search import OpenSearchCRUD

from common.rag_result import RagResult
from personaai_default import get_logger
from personaai_default.lib import get_root_path, get_question_nouns_sentence, getenv

from context_management.chromadb_context_updater import ChromadbContextUpdater
from langchain_loader.prompt_management.prompt_manage import PromptManage

log = get_logger()

root_path = get_root_path()

embeddings = get_embedding()

global vectordb
pettern = os.getenv('CATEGORY_PETTERN')

prompt_manager = PromptManage()

class RagService(Rag_stub.RagServicer):

    def __init__(self):
        self.executor = futures.ThreadPoolExecutor(max_workers=10)
        self.feature = None

    def Service(self, request, context):
        rag_result = RagResult.SUCCESS

        try:
            # ... 중략 ...

            log.info(f'명사 추출 결과: {nouns_query}')

            return response

            # log.info(result_documents)

        except FileNotFoundError as e:
            log.error(e)
            rag_result = RagResult.NOT_FOUND
        except ValueError as e:
            log.error(e)
            rag_result = RagResult.VALIDATION_ERROR

        return Rag_c.Response(object_result=rag_result.to_dict())

    def MultipleService(self, request, context):
        rag_result = RagResult.SUCCESS

        try:
            # ... 중략 ...

            return response

            # log.info(result_documents)

        except FileNotFoundError as e:
            log.error(e)
            rag_result = RagResult.NOT_FOUND
        except ValueError as e:
            log.error(e)
            rag_result = RagResult.VALIDATION_ERROR

        return Rag_c.Response(object_result=rag_result.to_dict())