import socket
import threading
import json
from socket import error

from pydantic import ValidationError

from app import utils
from app import schemas


HOST = '0.0.0.0'
PORT = 15000

ROOMS: list[schemas.Room] = []
PORTS: list[int] = []
STOP_FLAG = False


def register_available_port() -> int:
  for port in range(16000, 17000):
    if port not in PORTS:
      PORTS.append(port)
      return port


def handle_client(conn: socket.socket, addr: tuple[str, int]):
  try:
    while True:
      conn.send(json.dumps(
        [schemas.RoomView.model_validate(room.model_dump(exclude={'conns'})).model_dump()
         for room in ROOMS]).encode())

      try:
        action = schemas.RoomAction.model_validate_json(utils.recvall(conn))
      except ValidationError:
        conn.send(json.dumps({'status': 'error', 'msg': 'Wrong schema'}).encode())
        break
      except ConnectionResetError:
        break
      if action.type == schemas.ActionType.CREATE:
        handle_create_room(conn, action.username, action.data.id, action.data.size)
      elif action.type == schemas.ActionType.JOIN:
        handle_join_room(conn, action.username, action.data.id, action.data.invite_code)
  finally:
    conn.close()
    utils.info(f'Connection Closed : {addr[0]}:{addr[1]}')


def handle_create_room(conn: socket.socket, username: str, room_id: int, size: int):
  for room in ROOMS:
    if room.id == room_id:
      conn.send(json.dumps({'status': 'error', 'msg': 'Room exists'}).encode())
      return

  port = register_available_port()
  room = schemas.Room(id=room_id, port=port, invite_code=utils.generate_invite_code(), size=size, creator=username)
  ROOMS.append(room)

  threading.Thread(target=handle_chat_room, args=(room_id, size, port)).start()

  conn.send(json.dumps({'status': 'success'}).encode())
  handle_join_room(conn, username, room_id, room.invite_code)


def handle_join_room(conn: socket.socket, username: str, room_id: int, invite_code: str):
  room = None
  for room in ROOMS:
    if room.id == room_id:
      break
  if room is None:
    conn.send(json.dumps({'status': 'error', 'msg': 'Room not found'}).encode())
    return
  if room.invite_code != invite_code:
    conn.send(json.dumps({'status': 'error', 'msg': 'Wrong invite code'}).encode())
    return
  if len(room.users) >= room.size:
    conn.send(json.dumps({'status': 'error', 'msg': 'Room full'}).encode())
    return
  room.users.append(username)
  broadcast_user_joined(room_id, username)
  conn.send(json.dumps({'status': 'success', 'data': room.model_dump(exclude={'conns'})}).encode())


def handle_chat_room(room_id: int, size: int, port: int):
  for room in ROOMS:
    if room.id == room_id:
      break

  room_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    room_sock.settimeout(3)
    room_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    room_sock.bind((HOST, port))
    room_sock.listen(size)
    utils.success(f'Chat Room {room_id} Started : {HOST}:{port}')

    while not STOP_FLAG:
      try:
        conn, addr = room_sock.accept()
      except socket.timeout:
        continue

      room.conns.append(conn)
      utils.success(f'Room {room_id} New Connection : {addr[0]}:{addr[1]}')
      threading.Thread(target=handle_chat_client, args=(conn, room_id, addr)).start()
  finally:
    room_sock.close()
    utils.info(f'Chat Room {room_id} Stopped')


def handle_chat_client(conn: socket.socket, room_id: int, addr: tuple[str, int]):
  for room in ROOMS:
    if room.id == room_id:
      break

  try:
    while True:
      msg_action_json = utils.recvall(conn)
      if len(msg_action_json) == 0:
        break
      for client_conn in room.conns:
        if client_conn == conn:
          continue
        client_conn.send(msg_action_json)

  finally:
    room.conns.remove(conn)
    conn.close()
    utils.info(f'Room {room_id} Connection Closed : {addr[0]}:{addr[1]}')


def broadcast_user_joined(room_id: int, username: str):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    message = json.dumps({'room_id': room_id, 'username': username}).encode()
    sock.sendto(message, ('<broadcast>', 15000))

  finally:
    sock.close()


def main():
  global STOP_FLAG

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(20)
    utils.success(f'Server Started : {HOST}:{PORT}')

    while True:
      try:
        conn, addr = sock.accept()
        utils.success(f'New Connection : {addr[0]}:{addr[1]}')
        threading.Thread(target=handle_client, args=(conn, addr)).start()
      except KeyboardInterrupt:
        utils.logger_next_line()
        STOP_FLAG = True
        break
  finally:
    sock.close()
    utils.info('Server Stopped')


if __name__ == '__main__':
  main()
