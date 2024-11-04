import os
import re

import chromadb
from chromadb.db.base import UniqueConstraintError
from proto.py import Category_stub, Category_c

from common.category_result import CategoryResult
from config.function import Config, mkdir
from personaai_default import get_logger
from personaai_default.lib import get_root_path

log = get_logger()

config = Config()

persist_directory = os.path.join(get_root_path(), os.getenv('CHROMA_PERSIST_DIR'))

pettern = os.getenv('CATEGORY_PETTERN')

class Category(Category_stub.CategoryServicer):
    def Create(self, request, context):
        category_result = CategoryResult.SUCCESS
        try :
            # ... 중략 ...

        except PermissionError as e:
            category_result = CategoryResult.PERMISSION_ERROR
            log.error(e)
        except FileExistsError as e:
            category_result = CategoryResult.EXISTS
            log.error(e)
        except ValueError as e:
            category_result = CategoryResult.VALIDATION_ERROR
            log.error(e)
        except Exception as e:
            category_result = CategoryResult.FAIL
            log.error(e)

        return Category_c.Response(category_result=category_result.to_dict())

    def Delete(self, request, context):
        category_result = CategoryResult.SUCCESS
        try:
            # ... 중략 ...

        except PermissionError as e:
            category_result = CategoryResult.PERMISSION_ERROR
            log.error(e)
        except FileNotFoundError as e:
            category_result = CategoryResult.NOT_FOUND
            log.error(e)
        except ValueError as e:
            category_result = CategoryResult.VALIDATION_ERROR
            log.error(e)
        except Exception as e:
            category_result = CategoryResult.FAIL
            log.error(e)

        return Category_c.Response(category_result=category_result.to_dict())

    def CreateConfig(self, request, context):
        category_result = CategoryResult.SUCCESS
        try :
            if re.match(pettern, request.category) is None:
                raise ValueError('Invalid pettern')
            collection_path = f'{persist_directory}/{request.category}'
            # Chroma.
            mkdir(collection_path)
        except PermissionError as e:
            category_result = CategoryResult.PERMISSION_ERROR
            log.error(e)
        except Exception as e:
            category_result = CategoryResult.FAIL
            log.error(e)

        return Category_c.Response(category_result=category_result.to_dict())
