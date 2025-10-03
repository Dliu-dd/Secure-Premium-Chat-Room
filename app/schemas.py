import enum
import datetime

from pydantic import BaseModel, model_validator


class Room(BaseModel):
  id: int
  port: int
  invite_code: str
  size: int
  creator: str
  users: list[str] = []
  conns: list = []


class RoomView(BaseModel):
  id: int
  user_cnt: int
  size: int

  @model_validator(mode='before')
  @classmethod
  def setup_user_cnt(cls, data: dict):
    if data.get('users') is not None:
      data['user_cnt'] = len(data.get('users'))
    else:
      data['user_cnt'] = 0
    return data


class ActionType(enum.Enum):
  CREATE = 'CREATE'
  JOIN = 'JOIN'


class CreateRoomData(BaseModel):
  id: int
  size: int


class JoinRoomData(BaseModel):
  id: int
  invite_code: str


class RoomAction(BaseModel):
  type: ActionType
  username: str
  data: CreateRoomData | JoinRoomData


class MessageType(enum.Enum):
  MESSAGE = 'MESSAGE'
  FILE = 'FILE'
  EMOJI = 'EMOJI'
  HELLO = 'HELLO'


class MessageAction(BaseModel):
  type: MessageType
  data: str
