from dataclasses import dataclass


@dataclass(frozen=True)
class ComparisonRow:
    category: str
    metric: str
    pre_value: str
    post_value: str
    change: str
    status: str
    changed: bool
