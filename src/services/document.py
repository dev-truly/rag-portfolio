import os
import re

import chromadb
from dotenv import load_dotenv
from langchain.chains import LLMChain, StuffDocumentsChain, ReduceDocumentsChain, MapReduceDocumentsChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_loader import get_vectorstore, ChromaDocuments, get_embeddings
from langchain_loader.embeddings import get_embedding
from langchain_loader.handler.CallbackHandler import CallBackHandler
from langchain_text_splitters import CharacterTextSplitter
from personaai_default import get_logger
from personaai_default.lib import get_root_path, getenv
from proto.py import Document_stub, Document_c
from search import OpenSearchCRUD
from opensearchpy.helpers import bulk
import uuid

from torch.backends.mkl import verbose
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.trainer_callback import CallbackHandler

from common.document_result import DocumentResult
from convert.env_converter import EnvConverter
from exception.DocumentNotFoundError import DocumentNotFoundError
from exception.DocumentNotAllowedError import DocumentNotAllowedError
from personaai_default import get_logger
from personaai_default.lib import get_root_path, getenv
from langchain_loader.document.document_manage import DocumentManage
from langchain_loader.document.document_info_dto import RequestInfo

log = get_logger()

load_dotenv()

embeddings = get_embedding()

pettern = os.getenv('CATEGORY_PETTERN')

persist_directory = f"{get_root_path()}/{os.getenv('CHROMA_PERSIST_DIR')}"
document_file_path = f"{get_root_path()}/{os.getenv('DOCUMENT_DIR')}"

class Document(Document_stub.DocumentServicer):
    global ids

    def Embedder(self, request, context):
        chroma_documents = ChromaDocuments()
        document_result = DocumentResult.SUCCESS
        collection_path = f'{persist_directory}/{request.category}'

        try:
            # ... 중략 ...

            log.info('embedding clear')
            log.info('데이터 등록 성공')
        except ValueError as e:
            log.error(e)
            document_result = DocumentResult.VALIDATION_ERROR
        except DocumentNotFoundError as e:
            log.error(e)
            document_result = DocumentResult.DOCUMENT_NOT_FOUND
        except DocumentNotAllowedError as e:
            log.error(e)
            document_result = DocumentResult.DOCUMENT_NOT_ALLOWED
        except FileNotFoundError as e:
            log.error(e)
            document_result = DocumentResult.NOT_FOUND
        except Exception as e:
            log.error(e)
            document_result = DocumentResult.FAIL

        return Document_c.Response(document_result=document_result.to_dict())

    def Delete(self, request, context):
        document_result = DocumentResult.SUCCESS
        collection_path = f'{persist_directory}/{request.category}'

        try:
            # 문서 manager 생성
            doc_manager = DocumentManage(RequestInfo(request, document_file_path, collection_path))
            # 문서 업로드 & 요청 검증
            doc_manager.interceptor()

            client = OpenSearchCRUD(use_ssl=getenv('O_S_USE_SSL'))
            try:
                search_body = {
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {'file_name': request.kgpt_file_save_name}},
                                {"match": {'collection': request.category}}
                            ]
                        }
                    }
                }

                opensearch_result = client.client.delete_by_query(getenv('O_S_DOCUMENT_INDEX'), body=search_body)
                log.info(f'Opensearch Result: {opensearch_result}')
            except Exception as e:
                log.error(f"오픈서치 문서 페이지 삭제 실패({request.kgpt_file_save_name}, {request.category}): {e}")


            vectordb = get_vectorstore(
                collection_path=collection_path
            )

            metadata_query = {"source_save": request.kgpt_file_save_name}
            documents_to_delete = get_embeddings(vectordb, include=['metadatas'], where=metadata_query)

            if len(documents_to_delete.get('ids')) == 0:
                raise DocumentNotFoundError(f'DocumentNotFoundError search origin FileName: {request.kgpt_file_name}')

            print('delete target ids:', documents_to_delete['ids'])
            vectordb.delete(documents_to_delete['ids'])

            log.info('임베딩 문서 정상 삭제 완료: [파일명: %s]' % request.kgpt_file_name)

            log.info('데이터 삭제 성공')
        except ValueError as e:
            log.error(e)
            document_result = DocumentResult.VALIDATION_ERROR
        except DocumentNotFoundError as e:
            log.error(e)
            document_result = DocumentResult.DOCUMENT_NOT_FOUND
        except DocumentNotAllowedError as e:
            log.error(e)
            document_result = DocumentResult.DOCUMENT_NOT_ALLOWED
        except FileNotFoundError as e:
            log.error(e)
            document_result = DocumentResult.NOT_FOUND
        except Exception as e:
            log.error(e)
            document_result = DocumentResult.FAIL

        return Document_c.Response(document_result=document_result.to_dict())

    def EmbeddingList(self, request, context):
        log.info(request)
        document_result = DocumentResult.SUCCESS
        collection_path = f'{persist_directory}/{request.category}'
        document_list = []

        try:
            self.interceptor(request, collection_path)

            vectordb = get_vectorstore(
                collection_path=collection_path
            )

            embeddings = get_embeddings(vectordb)

            # 'page' 값을 기준으로 내림차순 정렬
            sorted_docs = sorted(embeddings['metadatas'], key=lambda x: x['page'], reverse=True)

            # 'page' 키를 'total_page' 키로 변경하면서 최대 페이지 데이터를 선택
            max_page_docs = {}
            for doc in sorted_docs:
                source = doc['source']
                if source not in max_page_docs:
                    max_page_docs[source] = doc
                    document_info = Document_c.DocumentInfo(
                        total_page=str(max_page_docs[source]['page']),
                        source=max_page_docs[source]['source'],
                        source_save=max_page_docs[source]['source_save'],
                        source_improved=max_page_docs[source]['source_improved']
                    )
                    document_list.append(document_info)
                    log.info(f"Selected max page doc for source {source}: {max_page_docs[source]}")


        except Exception as e:
            log.error(e)
            document_result = DocumentResult.FAIL

        # result_list = Document_c.DocumentList(document_info=document_list)

        # Response 생성
        response = Document_c.EmbeddingListResponse(
            result=document_result.result,
            status_code=document_result.status_code,
            description=document_result.description,
            document_info_list=document_list
        )

        return response

    def FullText(self, request, context):
        document_result = DocumentResult.SUCCESS
        document_path = f"{document_file_path}/{request.kgpt_file_save_name}"
        log.info(document_path)

        metadata = Document_c.Metadata(
            page_content="",
            page=0,
            source=document_path,
            score=0
        )
        try:
            # Initialize the loader
            loader = PyPDFLoader(document_path)

            # Load the PDF documents
            documents = loader.load()
            # self.summary(documents)
            # Concatenate text from all pages
            page_content = [document.page_content for document in documents]
            full_text = "\n".join(page_content)

            # Create metadata based on the extracted text
            if documents and len(documents) > 0:
                metadata = Document_c.Metadata(
                    page_content=full_text,  # Full text of the document
                    page=documents[0].metadata.get('page', 0),  # Ensure this is an integer
                    source=request.kgpt_file_name,
                    score=0
                )
            else:
                metadata = Document_c.Metadata(
                    page_content="",
                    page=0,
                    source=document_path,
                    score=0
                )
            # Create the response
            document_result = DocumentResult.SUCCESS
        except ValueError as e:
            log.error(e)
            document_result = DocumentResult.VALIDATION_ERROR
        except DocumentNotFoundError as e:
            log.error(e)
            document_result = DocumentResult.DOCUMENT_NOT_FOUND
        except DocumentNotAllowedError as e:
            log.error(e)
            document_result = DocumentResult.DOCUMENT_NOT_ALLOWED
        except FileNotFoundError as e:
            log.error(e)
            document_result = DocumentResult.NOT_FOUND
        except Exception as e:
            log.error(e)
            document_result = DocumentResult.FAIL
        finally:
            # Create the response
            response = Document_c.FullTextResponse()
            response.object_result.result = document_result.result
            response.object_result.status_code = document_result.status_code
            response.object_result.description = document_result.description
            response.object_result.metadata.CopyFrom(metadata)
            log.info(response)
            return response

