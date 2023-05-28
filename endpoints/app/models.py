import os
from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from app import db



class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page: int, per_page: int, endpoint, **kwargs):
        resources = query.paginate(page=page, per_page=per_page,
                                   error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

class Event(db.Model, PaginatedAPIMixin):
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