import tkinter as tk
import socket
import random
import threading

from frames.ip_search_frame import IPSearchFrame
from frames.waiting_frame import WaitingFrame
from frames.conversation_frame import ConversationFrame
from frames.conversation_history_frame import ConversationHistoryFrame
from frames.settings_frame import SettingsFrame

from conversation_history import ConversationHistory
from connection_handler import ConnectionHandler

from tkinter import *


class GUI(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)

        self.main_window = tk.Frame(self, width=555, height=555)
        self.main_window.pack_propagate(0)
        self.main_window.pack()
        self["bg"] = '#a3d4c5'

        self.conversationHistory = ConversationHistory()

        self.shared_data = {
            "host_ip": "",
            "host_port": "",
            "modulation_value": 0,
            "waiting_frame": {
                "not_accepted_flag": False,
                "stop_timer_flag": False
            },
            "conversation_flags": {
                "not_ended": True
            },
            "who_called": "",
            "cycle_ender": 0
        }

        self.frame_objects_list = (
            IPSearchFrame,
            WaitingFrame,
            ConversationFrame,
            ConversationHistoryFrame,
            SettingsFrame,
            ConnectionHandler
        )

        self.frame_objects_container = {}
        self.fill_frame_objects_container(self.frame_objects_list)

        self.show_frame("IPSearchFrame")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def fill_frame_objects_container(self, frame_objects):
        for FrameObject in frame_objects:
            frame_object_name = FrameObject.__name__
            frame_object = FrameObject(parent=self.main_window, controller=self)
            self.frame_objects_container[frame_object_name] = frame_object
            frame_object.grid(row=0, column=0, sticky="nsew")

    def return_to_main_frame(self):
        self["bg"] = '#a3d4c5'
        self.frame_objects_container["IPSearchFrame"].event_generate("<<ShowFrame>>")
        self.frame_objects_container["IPSearchFrame"].tkraise()

    def get_current_conversation(self):
        return self.frame_objects_container["ConversationFrame"].get_current_conversation()

    def new_cycle(self):
        return True if self.shared_data["cycle_ender"]  == "new_cycle" else False

    def close_conversation_frame(self):
        self.frame_objects_container["ConversationFrame"].return_to_main_frame()

    def show_frame(self, frame_object_name):
        frame_object = self.frame_objects_container[frame_object_name]
        frame_object.event_generate("<<ShowFrame>>")
        frame_object.tkraise()

    def on_closing(self):
        if tk.messagebox.askokcancel("Zakończ", "Czy na pewno chcesz wyjść z programu?"):
            self.frame_objects_container["ConnectionHandler"].thread_stopper["listener"] = True
            self.frame_objects_container["ConnectionHandler"].thread_stopper["clienter"] = True
            self.frame_objects_container["ConnectionHandler"].exit_listener()
            self.frame_objects_container["ConnectionHandler"].listener_socket.close()
            self.conversationHistory.saveConversationHistoryToFile()
            self.destroy()


if __name__ == '__main__':
    interface = GUI()
    interface.geometry("400x400")
    interface.title("TIP_Koziello_Chrul")
    interface.resizable(1,1)
    interface.mainloop()
