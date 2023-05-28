from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, String
from app import db


class Event(db.Model):
    __tablename__ = 'events'
    id = Column(BigInteger, primary_key=True)
    type = Column(String)
    repo_name = Column(String)
    created_at = Column(DateTime)

    def __hash__(self):
        return hash(self.id)
    
    def to_dict(self):
        data = {
            'id': self.id,
            'type': self.type,
            'repo_name': self.repo_name,
            'created_at': self.created_at.isoformat() + 'Z'
        }
        return data

    @staticmethod
    def from_dict(data):
        """
        Reconstructs the Event object from a dictionary
        """
        return Event(id=data['id'],
                     type=data['type'],
                     repo_name=data['repo_name'],
                     created_at=datetime.fromisoformat(data['created_at'][:-1]))


