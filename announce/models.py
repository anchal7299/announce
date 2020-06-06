from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    relationship,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
import bottle_tools as bt
from secrets import token_urlsafe
from announce import const

engine = create_engine(const.database_url)
Base = declarative_base()


class AnonUser:
    id = tg_handle = None


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    tg_handle = Column(String)

    def get_groups(self, session):
        return (
            session.query(Group)
            .join(Member)
            .filter(Member.user_id == self.id)
            .distinct()
        )


class Group(Base):
    __tablename__ = "group"
    name = Column(String)


class Member(Base):
    __tablename__ = "member"
    user_id = Column(Integer, ForeignKey("user.id"))
    group_id = Column(Integer, ForeignKey("group.id"))
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)


class Otp(Base):
    __tablename__ = "otp"
    id = Column(Integer, primary_key=True)
    tg_handle = Column(String)
    otp = Column(String)

    @staticmethod
    def loop_create(session, **kwargs):
        "Try to create a token and retry if uniqueness fails"
        while True:
            tok = Otp(otp=token_urlsafe(), **kwargs)
            session.add(tok)
            session.commit()
            return tok


class LoginToken(Base):
    __tablename__ = "logintoken"
    user_id = Column(Integer, ForeignKey("user.id"))
    token = Column(String, nullable=False, unique=True)
    has_logged_out = Column(Boolean, default=False)
    user = relationship("User")

    @staticmethod
    def loop_create(session, **kwargs):
        "Try to create a token and retry if uniqueness fails"
        while True:
            tok = LoginToken(token=token_urlsafe(), **kwargs)
            session.add(tok)
            session.commit()
            return tok


class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    path = Column(String)


class Cred(Base):
    __tablename__ = "creds"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    var = Column(String)
    group_id = Column(Integer, ForeignKey("image.id"))


class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    start = Column(DateTime)
    end = Column(DateTime)
    description = Column(String)
    image_id = Column(Integer, ForeignKey("image.id"))
    actions_done = Column(JSON)

    def asdict(self):
        return dict(
            eventid=self.id,
            title=self.title,
            end=self.start.to_iso8601_string(),
            end=self.end.to_iso8601_string(),
            description=self.description,
            imageid=self.image_id,
            actions_done=self.actions_done,
        )


Base.metadata.create_all(engine)
Session = sessionmaker(engine)
bt.common_kwargs.update({"Event": Event, "Image": Image})
