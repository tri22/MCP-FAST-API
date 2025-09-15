from datetime import datetime
import uuid
from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Text,
    Column,
    DateTime,
    Boolean,
    and_,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, email, name):
        self.email = email
        self.name = name


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, sender_id, subject, content, timestamp=None):
        self.sender_id = sender_id
        self.subject = subject
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()


class Recipient(Base):
    __tablename__ = "message_recipients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=False)
    read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    def __init__(self, message_id, recipient_id):
        self.message_id = message_id
        self.recipient_id = recipient_id


engine = create_engine("sqlite:///mydb.db", echo=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)


# ---------------- User APIs ----------------
def create_user(email: str, name: str):
    session = Session()
    new_user = User(email, name)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    session.close()
    return {"id": new_user.id, "email": new_user.email, "name": new_user.name}


def get_user_by_email(email: str):
    session = Session()
    user = session.query(User).filter(User.email == email).first()
    session.close()
    if not user:
        return None
    return {"id": user.id, "email": user.email, "name": user.name}


def get_all_users():
    session = Session()
    users = session.query(User).all()
    session.close()
    return [{"id": u.id, "email": u.email, "name": u.name} for u in users]


# ---------------- Message APIs ----------------
def send_message(sender_id: str, recipients: list[str], subject: str, content: str):
    session = Session()
    try:
        new_msg = Message(sender_id=sender_id, subject=subject, content=content)
        session.add(new_msg)
        session.flush()  # tạo id

        for r in recipients:
            new_recipient = Recipient(message_id=new_msg.id, recipient_id=r)
            session.add(new_recipient)

        session.commit()
        session.refresh(new_msg)
        return {
            "id": new_msg.id,
            "sender_id": new_msg.sender_id,
            "subject": new_msg.subject,
            "content": new_msg.content,
            "timestamp": new_msg.timestamp.isoformat(),
        }
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_sent_message(sender_id: str):
    session = Session()
    try:
        msgs = session.query(Message).filter(Message.sender_id == sender_id).all()
        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "subject": m.subject,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in msgs
        ]
    finally:
        session.close()


def view_inbox(user_id: str):
    session = Session()
    try:
        recipients = session.query(Recipient).filter(Recipient.recipient_id == user_id).all()
        results = []
        for r in recipients:
            msg = session.query(Message).filter(Message.id == r.message_id).first()
            results.append({
                "recipient_id": r.recipient_id,
                "message_id": r.message_id,
                "read": r.read,
                "read_at": r.read_at.isoformat() if r.read_at else None,
                "message": {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "subject": msg.subject,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } if msg else None
            })
        return results
    finally:
        session.close()


def get_unread_message(recipient_id: str):
    session = Session()
    try:
        msgs = session.query(Recipient).filter(
            and_(Recipient.recipient_id == recipient_id, Recipient.read == False)
        ).all()
        return [
            {
                "recipient_id": r.recipient_id,
                "message_id": r.message_id,
                "read": r.read,
                "read_at": r.read_at.isoformat() if r.read_at else None
            }
            for r in msgs
        ]
    finally:
        session.close()


def get_message_with_recipients(message_id: str):
    session = Session()
    try:
        recipients = session.query(Recipient).filter(Recipient.message_id == message_id).all()
        msg = session.query(Message).filter(Message.id == message_id).first()
        return {
            "message": {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "subject": msg.subject,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            } if msg else None,
            "recipients": [
                {
                    "recipient_id": r.recipient_id,
                    "read": r.read,
                    "read_at": r.read_at.isoformat() if r.read_at else None
                }
                for r in recipients
            ]
        }
    finally:
        session.close()


def mark_as_read(message_id: str, recipient_id: str):
    session = Session()
    try:
        session.query(Recipient).filter(
            Recipient.message_id == message_id,
            Recipient.recipient_id == recipient_id
        ).update(
            {Recipient.read: True, Recipient.read_at: datetime.utcnow()},
            synchronize_session=False
        )
        session.commit()
        r = session.query(Recipient).filter(
            Recipient.message_id == message_id,
            Recipient.recipient_id == recipient_id
        ).first()
        return {
            "recipient_id": r.recipient_id,
            "message_id": r.message_id,
            "read": r.read,
            "read_at": r.read_at.isoformat() if r.read_at else None
        }
    finally:
        session.close()
