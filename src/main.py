import os
import sys

from proto.py import Rag_stub, KgptLLM_stub, Category_stub, Document_stub
from server import add_servicers_to_server

import personaai_default as pdl
import kgpt_default
from services import *

from personaai_default import get_logger
import grpc
from concurrent import futures

log = get_logger()

def serve():
    pdl.splash_screen()
    log.info('PersonaAI LLM Version: v%s' % kgpt_default.__version__)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    try:
        servicers = [
            (Rag_stub, RagService, 'add_RagServicer_to_server'),
            (KgptLLM_stub, KgptLLM, 'add_KgptLLMServicer_to_server'),
            (Category_stub, Category, 'add_CategoryServicer_to_server'),
            (Document_stub, Document, 'add_DocumentServicer_to_server')
        ]

        add_servicers_to_server(server, servicers)

        server.add_insecure_port(f"0.0.0.0:{os.getenv('G_PORT')}")
        server.start()

        log.info(f"{os.getenv('SERVICE_NAME') if not os.getenv('SERVICE_NAME') is None else 'LLM'} Service start: {os.getenv('G_PORT')}")

        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)  # 서버 종료 시 server.pyfiles 프로세스도 종료합니다.


if __name__ == '__main__':
    serve()