import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Tags(SqlAlchemyBase):
    __tablename__ = 'tags'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    wallpaper_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("wallpapers.id"))
    wallpaper = orm.relation('WallPapers')
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')


    def __repr__(self):
        return f'<Tag> {self.id} {self.title} {self.wallpaper_id}'
