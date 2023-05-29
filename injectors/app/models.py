from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    id: int
    type: str
    repo_name: str
    created_at: datetime

    def __hash__(self):
        return hash(self.id)

    def to_dict(self):
        data = {
            "id": self.id,
            "type": self.type,
            "repo_name": self.repo_name,
            "created_at": self.created_at.isoformat() + "Z",
        }
        return data
