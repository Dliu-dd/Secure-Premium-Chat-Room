import os
import socket
import json
import subprocess
import tkinter as tk
from tkinter import messagebox

from app import utils
from app import schemas


HOST = '127.0.0.1'
PORT = 15000

ROOMS: list[schemas.Room] = []
IMG_PATH = os.path.join(os.path.dirname(__file__), 'img')


class RoundedFrame(tk.Frame):
  def __init__(self, parent, bg_color='#2B2D31', border_color='#40444B', **kwargs):
    super().__init__(parent, bg=bg_color, highlightbackground=border_color, 
                     highlightthickness=2, relief='solid', bd=0, **kwargs)
        
class StyledButton(tk.Button):
  def __init__(self, parent, **kwargs):
    if kwargs.get('cursor') is None:
      kwargs['cursor'] = 'hand2'
    if kwargs.get('font') is None:
      kwargs['font'] = ('Courier', 12, 'bold')
    super().__init__(parent, **kwargs)


class LandingUI:
  def __init__(self, sock: socket.socket):
    self.sock = sock
    self.window = tk.Tk()
    self.mode = tk.StringVar(value='create')
    self.layout()
    self.window.mainloop()

  def layout(self):
    self.window.title('Premium Chat Room | Welcome')
    self.window.configure(width=760, height=790, bg='#313338')
    self.window.resizable(width=False, height=False)

    self.main_frame = tk.Frame(self.window, bg='#313338')
    self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # Welcome section
    self.welcome_image = tk.PhotoImage(file=os.path.join(IMG_PATH, 'welcome.png'))
    self.welcome_image_label = tk.Label(self.main_frame, image=self.welcome_image, bg='#313338')
    self.welcome_image_label.grid(row=0, column=0, columnspan=2, pady=10)

    self.welcome_label = tk.Label(self.main_frame, text='Welcome to Premium Chat Room', font=('Courier', 20, 'bold'), bg='#313338', fg='whitesmoke')
    self.welcome_label.grid(row=1, column=0, columnspan=2, pady=25)

    # Username section (always visible)
    self.username_frame = tk.Frame(self.main_frame, bg='#2B2D31', highlightbackground='#40444B', highlightthickness=1)
    self.username_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=20, sticky='ew')
    
    # Configure grid weights for centering
    self.username_frame.grid_columnconfigure(0, weight=1)

    self.username_title = tk.Label(self.username_frame, text='User Information', font=('Courier', 14, 'bold'), bg='#2B2D31', fg='whitesmoke')
    self.username_title.grid(row=0, column=0, pady=(20, 10))

    # Username input container for centering
    self.username_input_frame = tk.Frame(self.username_frame, bg='#2B2D31')
    self.username_input_frame.grid(row=1, column=0, pady=(5, 25))

    self.name_label = tk.Label(self.username_input_frame, text='Username : ', font=('Courier', 12), bg='#2B2D31', fg='whitesmoke')
    self.name_label.grid(row=0, column=0, padx=(0, 5))

    self.name_entry = tk.Entry(self.username_input_frame, font=('Courier', 12), bg='#40444B', fg='whitesmoke', 
                               insertbackground='white', width=20, relief='solid', bd=1, highlightthickness=1,
                               highlightcolor='#5865F2', highlightbackground='#40444B')
    self.name_entry.grid(row=0, column=1)

    # Mode selection
    self.mode_frame = tk.Frame(self.main_frame, bg='#313338')
    self.mode_frame.grid(row=3, column=0, columnspan=2, pady=15)

    self.create_radio = tk.Radiobutton(self.mode_frame, text='Create Room', variable=self.mode, value='create',
                                       font=('Courier', 12), bg='#313338', fg='whitesmoke', selectcolor='#40444B',
                                       activebackground='#313338', activeforeground='whitesmoke', command=self.toggle_mode)
    self.create_radio.grid(row=0, column=0, padx=20)

    self.join_radio = tk.Radiobutton(self.mode_frame, text='Join Room', variable=self.mode, value='join',
                                     font=('Courier', 12), bg='#313338', fg='whitesmoke', selectcolor='#40444B',
                                     activebackground='#313338', activeforeground='whitesmoke', command=self.toggle_mode)
    self.join_radio.grid(row=0, column=1, padx=20)

    # Create Room Frame
    self.create_frame = RoundedFrame(self.main_frame, bg_color='#2B2D31', border_color='#40444B')
    self.create_frame.grid(row=4, column=0, columnspan=2, pady=10, padx=20, sticky='ew')
    
    # Configure grid weights for centering
    self.create_frame.grid_columnconfigure(0, weight=1)

    self.create_title = tk.Label(self.create_frame, text='Create New Room', font=('Courier', 14, 'bold'), bg='#2B2D31', fg='whitesmoke')
    self.create_title.grid(row=0, column=0, pady=(15, 10))

    # Create input container for centering Room ID and Room Size as a group
    self.create_input_frame = tk.Frame(self.create_frame, bg='#2B2D31')
    self.create_input_frame.grid(row=1, column=0, pady=(5, 10), padx=(32, 32), sticky='w')

    # Room ID row
    self.create_room_id_container = tk.Frame(self.create_input_frame, bg='#2B2D31')
    self.create_room_id_container.grid(row=0, column=0, pady=5, sticky='w')

    self.create_room_id_label = tk.Label(self.create_room_id_container, text='Room ID : ', font=('Courier', 12), bg='#2B2D31', fg='whitesmoke')
    self.create_room_id_label.grid(row=0, column=0, padx=(0, 5))

    self.create_room_id_entry = tk.Entry(self.create_room_id_container, font=('Courier', 12), bg='#40444B', fg='whitesmoke', 
                                         insertbackground='whitesmoke', width=20, relief='solid', bd=1, highlightthickness=1,
                                         highlightcolor='#5865F2', highlightbackground='#40444B')
    self.create_room_id_entry.grid(row=0, column=1)

    # Room Size row
    self.create_room_size_container = tk.Frame(self.create_input_frame, bg='#2B2D31')
    self.create_room_size_container.grid(row=1, column=0, pady=5, sticky='w')

    self.create_room_size_label = tk.Label(self.create_room_size_container, text='Room Size : ', font=('Courier', 12), bg='#2B2D31', fg='whitesmoke')
    self.create_room_size_label.grid(row=0, column=0, padx=(0, 5))

    self.create_room_size_var = tk.StringVar(self.window)
    self.create_room_size_var.set('2')
    
    # Styled dropdown
    self.create_room_size_dropdown = tk.OptionMenu(self.create_room_size_container, self.create_room_size_var, '2', '3', '4')
    self.create_room_size_dropdown.configure(font=('Courier', 12), bg='#2B2D31', fg='whitesmoke', width=17,
                                             relief='solid', bd=1, highlightthickness=0, activebackground='#5865F2')
    self.create_room_size_dropdown.grid(row=0, column=1)

    # Styled create button
    self.create_button = StyledButton(self.create_frame, text='Create Room', fg='black', width=20, height=2, command=self.create_room)
    self.create_button.grid(row=2, column=0, pady=(10, 20))

    # Join Room Frame
    self.join_frame = RoundedFrame(self.main_frame, bg_color='#2B2D31', border_color='#40444B')
    self.join_frame.grid(row=5, column=0, columnspan=2, pady=10, padx=20, sticky='ew')
    
    # Configure grid weights for centering
    self.join_frame.grid_columnconfigure(0, weight=1)

    self.join_title = tk.Label(self.join_frame, text='Join Existing Room', font=('Courier', 14, 'bold'), bg='#2B2D31', fg='whitesmoke')
    self.join_title.grid(row=0, column=0, pady=(15, 10))

    # Join input container for centering Room ID and Invite Code as a group
    self.join_input_frame = tk.Frame(self.join_frame, bg='#2B2D31')
    self.join_input_frame.grid(row=1, column=0, pady=(5, 10), padx=(32, 32), sticky='w')

    # Room ID row
    self.join_room_id_container = tk.Frame(self.join_input_frame, bg='#2B2D31')
    self.join_room_id_container.grid(row=0, column=0, pady=5, sticky='w')

    self.join_room_id_label = tk.Label(self.join_room_id_container, text='Room ID : ', font=('Courier', 12), bg='#2B2D31', fg='whitesmoke')
    self.join_room_id_label.grid(row=0, column=0, padx=(0, 5))

    self.join_room_id_entry = tk.Entry(self.join_room_id_container, font=('Courier', 12), bg='#40444B', fg='whitesmoke', 
                                       insertbackground='whitesmoke', width=18, relief='solid', bd=1, highlightthickness=1,
                                       highlightcolor='#5865F2', highlightbackground='#40444B')
    self.join_room_id_entry.grid(row=0, column=1)

    # Invite Code row
    self.join_invite_code_container = tk.Frame(self.join_input_frame, bg='#2B2D31')
    self.join_invite_code_container.grid(row=1, column=0, pady=5, sticky='w')

    self.join_invite_code_label = tk.Label(self.join_invite_code_container, text='Invite Code : ', font=('Courier', 12), bg='#2B2D31', fg='whitesmoke')
    self.join_invite_code_label.grid(row=0, column=0, padx=(0, 5))

    self.join_invite_code_entry = tk.Entry(self.join_invite_code_container, font=('Courier', 12), bg='#40444B', fg='whitesmoke', 
                                           insertbackground='whitesmoke', width=18, relief='solid', bd=1, highlightthickness=1,
                                           highlightcolor='#5865F2', highlightbackground='#40444B')
    self.join_invite_code_entry.grid(row=0, column=1)

    # Styled join button
    self.join_button = StyledButton(self.join_frame, text='Join Room', fg='black', width=20, height=2, command=self.join_room)
    self.join_button.grid(row=2, column=0, pady=(10, 20))

    # Status label
    self.status_label = tk.Label(self.main_frame, text='', font=('Courier', 12), bg='#313338', fg='#FAA61A')
    self.status_label.grid(row=6, column=0, columnspan=2, pady=10)

    # Initialize with create mode
    self.toggle_mode()

  def toggle_mode(self):
    if self.mode.get() == 'create':
      self.create_frame.grid()
      self.join_frame.grid_remove()
    else:
      self.create_frame.grid_remove()
      self.join_frame.grid()

  def create_room(self):
    global ROOMS

    username = self.name_entry.get().strip()
    room_id = self.create_room_id_entry.get().strip()
    room_size = self.create_room_size_var.get().strip()
    if len(username) == 0 or len(room_id) == 0 or len(room_size) == 0:
      return
    if (not room_id.isdigit()) or (not room_size.isdigit()):
      return
    action = schemas.RoomAction(type=schemas.ActionType.CREATE, username=username, data=schemas.CreateRoomData(id=int(room_id), size=int(room_size)))
    self.sock.send(action.model_dump_json().encode())
    res = json.loads(utils.recvall(self.sock))
    if res['status'] != 'success':
      ROOMS = [schemas.RoomView.model_validate(room) for room in json.loads(utils.recvall(self.sock))]
      messagebox.showerror('Error', res['msg'])
      return
    subprocess.Popen(['poetry', 'run', 'chatroom', username, json.dumps(json.loads(utils.recvall(self.sock).decode())['data'])])

    ROOMS = [schemas.RoomView.model_validate(room) for room in json.loads(utils.recvall(self.sock))]


  def join_room(self):
    global ROOMS

    username = self.name_entry.get().strip()
    room_id = self.join_room_id_entry.get().strip()
    invite_code = self.join_invite_code_entry.get().strip()
    if len(username) == 0 or len(room_id) == 0 or len(invite_code) == 0:
      return
    action = schemas.RoomAction(type=schemas.ActionType.JOIN, username=username, data=schemas.JoinRoomData(id=int(room_id), invite_code=invite_code))
    self.sock.send(action.model_dump_json().encode())
    res = json.loads(utils.recvall(self.sock))
    if res['status'] == 'error':
      messagebox.showerror('Error', res['msg'])
      ROOMS = [schemas.RoomView.model_validate(room) for room in json.loads(utils.recvall(self.sock))]
      return
    subprocess.Popen(['poetry', 'run', 'chatroom', username, json.dumps(res['data'])])

    ROOMS = [schemas.RoomView.model_validate(room) for room in json.loads(utils.recvall(self.sock))]


def main():
  global ROOMS

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sock.connect((HOST, PORT))

    ROOMS = [schemas.RoomView.model_validate(room) for room in json.loads(utils.recvall(sock))]

    LandingUI(sock)

  finally:
    sock.close()


if __name__ == '__main__':
  main()
