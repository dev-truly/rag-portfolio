from common.grpc_enum import GrpcEnum

class DocumentResult(GrpcEnum):
    SUCCESS = (True, "success", "정상 처리 완료")
    NOT_FOUND = (False, "not_found", "존재 하지 않는 컬렉션")
    DOCUMENT_NOT_FOUND = (False, "document_not_found", "존재 하지 않는 문서")
    DOCUMENT_NOT_ALLOWED = (False, "document_not_allowed", "허용되지 않는 문서")
    PERMISSION_ERROR = (False, "permission_error", "권한이 없습니다.")
    VALIDATION_ERROR = (False, "validation_error", "카테고리 패턴 형식과 다른 패턴 입니다.")
    FAIL = (False, "fail", "작업 실패 했습니다.")