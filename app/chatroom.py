import os
import sys
import socket
import threading
import datetime
import zoneinfo
import time
import tkinter as tk
from tkinter import filedialog

from app import schemas
from app import utils


STOP_FLAG = False
IMG_PATH = os.path.join(os.path.dirname(__file__), 'img')


class ChatRoom:
  def __init__(self, username: str, room: schemas.Room):
    global STOP_FLAG

    self.username = username
    self.room = room

    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.connect(('127.0.0.1', room.port))
    self.sock.send(schemas.MessageAction(type=schemas.MessageType.HELLO, data=username).model_dump_json().encode())
    threading.Thread(target=self.message_receive).start()

    self.window = tk.Tk()
    self.layout()
    self.window.mainloop()

    self.sock.close()
    STOP_FLAG = True
    time.sleep(3.5)

  def layout(self):
    self.window.title(f'Premium Chat Room | @{self.username}')
    self.window.configure(width=800, height=600, bg='#313338')
    self.window.resizable(width=False, height=False)

    # 左側好友列表
    self.left_frame = tk.Frame(self.window, bg='#2f3136', width=200)
    self.left_frame.place(relheight=1, relwidth=0.25)

    self.labelFriends = tk.Label(self.left_frame, text='Room Users', font=('Courier', 12, 'bold'), bg='#2f3136', fg='#b4b4b4')
    self.labelFriends.pack(pady=(7, 6))

    self.friends_listbox = tk.Listbox(self.left_frame, bg='#2f3136', fg='white', font=('Courier', 13), selectbackground='#4f545c', highlightbackground='#777', highlightthickness=1)
    self.friends_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    for user in self.room.users:
      self.friends_listbox.insert(tk.END, ' ' + user)

    # 中間聊天區
    self.middle_frame = tk.Frame(self.window, bg='#36393f')
    self.middle_frame.place(relheight=0.93, relwidth=0.75, relx=0.25)

    self.labelHead = tk.Label(self.middle_frame, text=f'Room {self.room.id} | Invite Code : {self.room.invite_code}', font=('Courier', 16, 'bold'), bg='#36393f', fg='white')
    self.labelHead.pack(anchor='nw', padx=10, pady=(7, 3))

    # 聊天室
    self.text_area = tk.Text(self.middle_frame, bg='#36393f', fg='white', font=('Courier', 11), state=tk.DISABLED, wrap=tk.WORD, highlightbackground='#777', highlightthickness=1)
    self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=(3, 10))

    # 底部訊息輸入欄
    self.bottom_frame = tk.Frame(self.window, bg='#40444b')
    self.bottom_frame.place(relx=0.25, rely=0.93, relwidth=0.75, relheight=0.06)

    self.send_file_img = tk.PhotoImage(file=os.path.join(IMG_PATH, 'plus.png')).subsample(32, 32)
    self.button1 = tk.Button(self.bottom_frame, width=14.5, height=14.5, bg='#40444b', border=0, image=self.send_file_img, command=self.send_file)
    self.button1.pack(side=tk.LEFT, padx=(13, 3), pady=6)

    self.entry_message = tk.Entry(self.bottom_frame, bg='#40444b', fg='white', font=('Courier', 9))
    self.entry_message.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3, pady=3)

    self.send_msg_img = tk.PhotoImage(file=os.path.join(IMG_PATH, 'send.png')).subsample(32, 32)
    self.send_msg_button = tk.Button(self.bottom_frame, width=14.5, height=14.5, bg='#40444b', border=0, image=self.send_msg_img, command=lambda: self.send_message())
    self.send_msg_button.pack(side=tk.LEFT, padx=3, pady=6)

    self.send_emoji_img = tk.PhotoImage(file=os.path.join(IMG_PATH, 'emoji.png')).subsample(32, 32)
    self.send_emoji_button = tk.Button(self.bottom_frame, width=14.5, height=14.5, bg='#40444b', border=0, image=self.send_emoji_img, command=self.send_emoji)
    self.send_emoji_button.pack(side=tk.LEFT, padx=(3, 13), pady=6)

  def message_receive(self):
    while not STOP_FLAG:
      self.sock.settimeout(3)
      try:
        message_action = schemas.MessageAction.model_validate_json(utils.recvall(self.sock))
      except socket.timeout:
        continue
      if message_action.type == schemas.MessageType.HELLO:
        self.friends_listbox.insert(tk.END, ' ' + message_action.data)
      elif message_action.type == schemas.MessageType.MESSAGE:
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, message_action.data)
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)
      elif message_action.type == schemas.MessageType.FILE:
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, message_action.data)
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)
      elif message_action.type == schemas.MessageType.EMOJI:
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, message_action.data)
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)


  def send_file(self):
    ts = datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S')
    filepath = filedialog.askopenfilename()
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    payload = (f' {self.username}      {ts}\n' +
               ' ' + '+' * 48 + '\n' + 
               f'  File : {filename}\n'
               f'  Size : {filesize} bytes\n\n\n')
    self.sock.send(schemas.MessageAction(type=schemas.MessageType.MESSAGE, data=payload).model_dump_json().encode())
    self.text_area.config(state=tk.NORMAL)
    self.text_area.insert(tk.END, payload)
    self.text_area.config(state=tk.DISABLED)
    self.text_area.see(tk.END)
    self.entry_message.delete(0, tk.END)


  def send_message(self):
    message = self.entry_message.get()
    message = '\n'.join('  ' + message[i: i + 46] for i in range(0, len(message), 46))
    ts = datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S')
    payload = (f' {self.username}      {ts}\n' +
               ' ' + '+' * 48 + '\n' + 
               f'{message}\n\n\n')
    self.sock.send(schemas.MessageAction(type=schemas.MessageType.MESSAGE, data=payload).model_dump_json().encode())

    self.text_area.config(state=tk.NORMAL)
    self.text_area.insert(tk.END, payload)
    self.text_area.config(state=tk.DISABLED)
    self.text_area.see(tk.END)
    self.entry_message.delete(0, tk.END)


  def send_emoji(self):
    message = self.entry_message.get()
    message = '\n'.join('  ' + message[i: i + 46] for i in range(0, len(message), 46))
    ts = datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Taipei')).strftime('%Y/%m/%d %H:%M:%S')
    payload = (f' {self.username}      {ts}\n' +
               ' ' + '+' * 48 + '\n' + 
               f'{message}\n\n\n')
    self.sock.send(schemas.MessageAction(type=schemas.MessageType.MESSAGE, data=payload).model_dump_json().encode())

    self.text_area.config(state=tk.NORMAL)
    self.text_area.insert(tk.END, payload)
    self.text_area.config(state=tk.DISABLED)
    self.text_area.see(tk.END)
    self.entry_message.delete(0, tk.END)


def main():
  ChatRoom(sys.argv[1], schemas.Room.model_validate_json(sys.argv[2]))


if __name__ == '__main__':
  main()
