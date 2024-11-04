from dataclasses import dataclass

@dataclass
class Metadata:
    page_content: str
    page: int
    source: str
    score: float=0.0