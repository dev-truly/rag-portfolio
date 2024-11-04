from enum import Enum


class GrpcEnum(Enum):
    def __init__(self, result, status_code, description):
        self.result = result
        self.status_code = status_code
        self.description = description

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def lower_status_code(self):
        return self.status_code.lower()