import logging
import sys
import socket
import random
import string


logger = logging.getLogger('ctflib-logger')
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(stdout_handler)


def info(msg: str):
  logger.info(f'[\033[34m*\033[0m] {msg}')


def success(msg: str):
  logger.info(f'[\033[32m+\033[0m] {msg}')


def warning(msg: str):
  logger.warning(f'[\033[33m#\033[0m] {msg}')


def error(msg: str):
  logger.error(f'[\033[31m!\033[0m] {msg}')


def logger_next_line():
  logger.info('')


def recvall(sock: socket.socket):
  buffer = b''
  while True:
    temp = sock.recv(4096)
    buffer += temp
    if len(temp) < 4096:
      return buffer


def generate_invite_code() -> str:
  return ''.join(random.choices(string.digits, k=6))
