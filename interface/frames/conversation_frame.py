import tkinter as tk
import time

from tkinter import *


class ConversationFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        # Controller from parent element (can turn frames)
        self.controller = controller
        self["bg"] = '#a3d4c5'

        # Dictionary that holds flags
        self.flags = {
            "pause_counter": 0
        }

        # Bind ShowFrame event to on_show function
        self.bind("<<ShowFrame>>", self.on_show)

        self.title = tk.Label(self, background="#a3d4c5", text="Trwa rozmowa...")
        self.title.pack()

        # Receiver label
        self.receiver_label = tk.Label(self, background="#a3d4c5", text="")

        # Is modulation active
        self.modulation_label = tk.Label(self, background="#a3d4c5", text="")
        self.modulation_label.pack()

        # Timer that holds conversation time
        self.conversation_timer = tk.Label(self, background="#a3d4c5", text="")
        self.conversation_timer_info = [0, 0, 0]

        # Label that states who has a right to talk right now
        self.who_talks_label = tk.Label(self, background="#a3d4c5", text="")

        self.modulation_scale = tk.Scale(self, orient="horizontal", background="#a3d4c5", from_=-5, to=5)
        self.modulation_scale.set(self.controller.shared_data["modulation_value"])

        modulation_button = tk.Button(self, text="Ustaw", background="#a3d4c5", command=self.set_modulation_value)

        self.modulation_label = tk.Label(self, text="Wartosc modulacji: {}".format(self.modulation_scale.get()), background="#a3d4c5")

        self.modulation_label.pack(side="bottom")
        modulation_button.pack(side="bottom")
        self.modulation_scale.pack(side="bottom")

    def set_modulation_value(self):
        self.controller.shared_data["modulation_value"] = self.modulation_scale.get()
        self.modulation_label.configure(text="Wartosc modulacji: {}".format(self.modulation_scale.get()))

    def new_conversation(self):
        return self.controller.conversationHistory.newConversation()

    def set_caller(self):
        self.who_talks_label.pack()
        if self.controller.shared_data["who_called"] == "me":
            self.who_talks_label.configure(text="Nadawca (ja)")
        else:
            self.who_talks_label.configure(text="Nadawca")
        self.controller["bg"] = '#00b894'
        # self.flags["who_talks_flag"] = not self.flags["who_talks_flag"]
        self.flags["who_talks_flag"] = "caller"

    def set_receiver(self):
        self.who_talks_label.pack()
        if self.controller.shared_data["who_called"] == "you":
            self.who_talks_label.configure(text="Odbierający (ja)")
        else:
            self.who_talks_label.configure(text="Odbierający")
        self.controller["bg"] = '#e17055'
        # self.flags["who_talks_flag"] = not self.flags["who_talks_flag"]
        self.flags["who_talks_flag"] = "receiver"

    # Part responsible for conversation timer
    pattern = '{0:02d}:{1:02d}:{2:02d}'

    # Decide whether it's time for me or recipient to talk
    def conversation_timer_after_cycle(self):
        if self.conversation_timer_info[2] == 0 or self.conversation_timer_info[2] == 30:
            return True
        else:
            return False

    # Handle conversation timer
    def update_conversation_timer(self, is_ended=False):
        if not is_ended:
            # If it's not stopped
            if self.flags["conversation_timer_running_flag"]:
                # Decide whose time it is to talk
                if self.controller.new_cycle():
                    self.controller.shared_data["cycle_ender"] = "cycle_ended"

                    if self.flags["who_talks_flag"] == "receiver":
                        self.set_caller()
                    else:
                        self.set_receiver()

                # Increment conversation timer data
                self.conversation_timer_info[2] += 1

                # If 60 seconds passed, zero the value and increment minutes
                if self.conversation_timer_info[2] >= 60:
                    self.conversation_timer_info[2] = 0
                    self.conversation_timer_info[1] += 1

                # If 60 minutes passed, zero the value and increment hours
                if self.conversation_timer_info[1] >= 60:
                    self.conversation_timer_info[0] += 1
                    self.conversation_timer_info[1] = 0

                # Format time_string in regards to pattern
                time_string = self.pattern.format(self.conversation_timer_info[0],
                                                  self.conversation_timer_info[1],
                                                  self.conversation_timer_info[2])
                return time_string
        else:
            time_string = self.pattern.format(self.conversation_timer_info[0],
                                              self.conversation_timer_info[1],
                                              self.conversation_timer_info[2])
            return time_string

    # Handle conversation timer
    def set_conversation_timer(self):
        if self.flags["conversation_timer_working_flag"]:
            # Update timer with formatted pattern timer value
            self.conversation_timer.configure(text=self.update_conversation_timer())
            # Set new value after 1000 ms
            self.after(1000, self.set_conversation_timer)
        else:
            return

    # To stop conversation timer
    def stop_conversation_timer(self):
        self.flags["conversation_timer_running_flag"] = False

    # To start conversation timer
    def start_conversation_timer(self):
        self.flags["conversation_timer_running_flag"] = True

    def kill_conversation_timer(self):
        self.flags["conversation_timer_working_flag"] = False
        self.conversation_timer.pack_forget()

    def return_to_main_frame(self):
        tk.messagebox.showinfo("Zakończ", "Połączenie zakończone.")
        self.receiver_label.pack_forget()
        self.kill_conversation_timer()
        self.conversation["duration"] = self.update_conversation_timer(True)
        self.conversation["status"] = "ended"
        self.controller.conversationHistory.addConversation(self.conversation)
        self.conversation_timer_info = [0, 0, 0]
        self.controller.return_to_main_frame()
        self.pack_forget()

    def on_show(self, event):
        self.flags["conversation_timer_running_flag"] = True
        self.flags["conversation_timer_working_flag"] = True
        if self.controller.shared_data["modulation_value"] != 0:
            self.modulation_label.configure(text="Modulacja jest aktywna - wartosc: {}".format(self.controller.shared_data["modulation_value"]))
        else:
            self.modulation_label.configure(text="Modulacja nie jest aktywna")

        self.flags["who_talks_flag"] = "receiver"
        self.conversation = self.new_conversation()
        self.conversation["status"] = "in progress"
        self.conversation_timer.pack()
        self.set_conversation_timer()

    def get_current_conversation(self):
        return self.conversation