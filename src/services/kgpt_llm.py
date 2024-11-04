import copy
import os
import queue
import re
import unicodedata
from concurrent import futures

import chromadb
import grpc
from langchain.chains import LLMChain
from langchain.prompts import load_prompt
from langchain_core.runnables import RunnablePassthrough
from langchain_loader import get_vectorstore
from langchain_loader.chains import invoke_qa
from langchain_loader.context_management import ContextUpdater
from langchain_loader.embeddings import get_embedding
from langchain_loader.handler.CallbackHandler import CallBackHandler
from langchain_loader.vectorstores import as_retriever
from langchain_openai import ChatOpenAI
from langchain_stream import Manage
from personaai_default import get_logger, get_question_nouns_sentence
from personaai_default.lib import get_root_path, getenv, search_text, get_cleaned_text
from proto.py import KgptLLM_stub, KgptLLM_c
from search import OpenSearchCRUD

from common.kgpt_llm_result import KgptLLMResult
from config.function import Config
from context_management.chromadb_context_updater import ChromadbContextUpdater
from langchain_loader.prompt_management.prompt_manage import PromptManage

log = get_logger()
config = Config()

root_path = get_root_path()

embeddings = get_embedding()

# 사용자의 질문으로 회의 회수를 구한 것으로 회의록 파일을 찾음
def find_file_with_prompt(directory, keyword):
    # 디렉토리 내 모든 파일에 대해 반복
    for filename in os.listdir(directory):
        # 파일 이름에 키워드가 포함되어 있는지 확인

        unicode_keyword = unicodedata.normalize('NFC', keyword)
        unicode_filename = unicodedata.normalize('NFC', filename)

        if unicode_keyword in unicode_filename:
            # 키워드를 포함한 첫 번째 파일의 경로를 반환
            return_path = os.path.join(directory, filename)
            log.info(return_path)
            return return_path

    # 키워드를 포함한 파일을 찾지 못한 경우 None을 반환
    return None

def process_llm_response(llm_response):
    log.info('\n\nSources:')
    for source in llm_response["source_documents"]:
        log.info(source.metadata['source'])

client_instance = {}

pettern = os.getenv('CATEGORY_PETTERN')
prompt_path = f'{root_path}/src/promptfiles/'

manage = Manage()
class KgptLLM(KgptLLM_stub.KgptLLMServicer):
    global vectordb

    def __init__(self):
        self.executor = futures.ThreadPoolExecutor(max_workers=10)
        self.feature = None

    def Service(self, request, context):
        try:
            chroma = get_vectorstore(
                db_type='Chroma',
                collection_path = collection_path,
                embeddings=embeddings,
            )

            results1 = chroma.search(query=prompt_updated, search_type="similarity")
            results2 = chroma.search(query=nouns_query, search_type="similarity")

            # Document 객체의 특정 속성을 기준으로 tuple을 생성하고 집합으로 변환
            set1 = {(doc.metadata['page'], doc.metadata['source_save']): doc for doc in results1}
            set2 = {(doc.metadata['page'], doc.metadata['source_save']): doc for doc in results2}

            # 두 집합의 합집합을 구함 (중복되지 않도록)
            combined_dict = {**set1, **set2}

            # 합집합 결과를 Document 객체로 복원
            search_document_list = list(combined_dict.values())

            context_updater:ContextUpdater = ChromadbContextUpdater(search_client, search_document_list)
            # document_list = get_page_context(search_client, search_document_list)
            if getenv('IS_CONTEXTUAL_CHUNKS'):
                context_updater.set_contextual_chunks()
            document_list = context_updater.return_search_document_list
            document_text = '\n'.join([metadata.page_content for metadata in document_list])

            if client_instance.get(request.clientid) is None:
                log.debug(f"{request.clientid}: 클라이언트 최초 연결 확인")
                # ... 중략 ...

            if document_list:
                sorted_data = sorted(document_list, key=lambda x: (x.metadata['source'], x.metadata['page']))
                for metadata in sorted_data:
                    return_metadata = "{'metadata': %s, 'page_content': '%s'}" % (metadata.metadata, metadata.page_content.replace("'", "\\'"))
                    manage.get(request.clientid).put(return_metadata.replace("'", '"'))

            self.feature = self.executor.submit(invoke_qa, {'context': document_text, 'question': prompt_updated}, qa, manage.get(request.clientid))

            is_stream = True
            token_list = []
            while is_stream:
                if manage.get(request.clientid) is None:
                    break

                try:
                    token = manage.get(request.clientid).get(timeout=0.5)

                    if token == 'end':
                        token = 'end queue'
                        is_stream = False
                    if token is None:
                        break

                    token_list.append(token)
                    # 응답 처리
                    yield KgptLLM_c.StreamResponse(object_result={"result": True, "status_code": "success", "message": token})

                except queue.Empty:
                    continue

            log.info(f'[human]: {request.prompt}\n[ai]: {"".join(token_list)}\n')
        except FileNotFoundError as e:
            log.error(e)
            yield KgptLLM_c.StreamResponse(object_result={"result": False, "status_code": "not_found", "message": "존재 하지 않는 컬렉션"})
        except ValueError as e:
            log.error(e)
            yield KgptLLM_c.StreamResponse(object_result={"result": False, "status_code": "validation_error", "message": ""})
        except Exception as e:
            log.error(e)
            yield KgptLLM_c.StreamResponse(object_result={"result": False, "status_code": "exception", "message": ""})

        except grpc.RpcError as e:
            self.destory_instance(request.clientid)

            log.debug(f"{request.clientid}: exception 클라이언트 연결 종료 감지")

    def ClientDisconnect(self, request, context):
        result = KgptLLMResult.SUCCESS

        self.destory_instance(request.clientid)
        msg = f"{request.clientid}: 클라이언트 연결 종료"
        log.debug(msg)

        return KgptLLM_c.Response(object_result=result.to_dict())


    def CancelQueue(self, request, context):
        result = KgptLLMResult.SUCCESS

        log.info(request.clientid)
        if client_instance.get(request.clientid) is not None:
            manage.put(request.clientid, 'end')
            manage.put(request.clientid, 'None')
            manage.clear(request.clientid)
            manage.remove(request.clientid)
            client_instance[request.clientid]['llm'].callbacks[0].stop()
            client_instance[request.clientid]['llm'] = None
            client_instance[request.clientid]['qa'] = None
            client_instance[request.clientid] = None
            self.feature.cancel()

        return KgptLLM_c.Response(object_result=result.to_dict())

    def destory_instance(self, clientid):
        if client_instance.get(clientid) is not None:
            manage.put(clientid, 'None')
            manage.clear(clientid)

