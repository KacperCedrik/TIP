import tkinter as tk
import time


class WaitingFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        # Controller from parent element (can turn frames)
        self.controller = controller
        self["bg"] = '#a3d4c5'

        # Dictionary that holds flags
        self.flags = {}

        # Bind ShowFrame event to on_show function
        self.bind("<<ShowFrame>>", self.on_show)

        # Return button
        return_button = tk.Button(self, text="Wróć do poprzedniej strony", command=lambda: self.return_to_main_frame())
        return_button.pack(side="bottom")

        # Accept connection - testing purposes ######
        accept_connection_button = tk.Button(self, text="Przejdz do polaczenia", command=lambda: self.accept_connection())
        accept_connection_button.pack(side="bottom")
        #############################################

        # Receiver label declaration
        self.receiver_label = tk.Label(self, background="#a3d4c5", text="")

        # Timer declaration
        self.timer = tk.Label(self, background="#a3d4c5", text="30")

    # Restarts the timer to 30 seconds mark
    def restart_timer(self):
        self.timer.configure(text=30)

    # Sets stop_timer_flag and restarts the timer
    def stop_timer(self):
        self.controller.shared_data["waiting_frame"]["stop_timer_flag"] = True
        self.restart_timer()
        self.timer.pack_forget()

    # Temporary functionality that transports to ConversationFrame
    def accept_connection(self):
        self.stop_timer()
        self.controller.show_frame("ConversationFrame")

    # Go back to main frame
    def return_to_main_frame(self):
        self.stop_timer()
        self.controller.return_to_main_frame()

    # Run in case user refuses to connect
    def show_not_accepted_message(self):
        if self.controller.shared_data["waiting_frame"]["not_accepted_flag"]:
            tk.messagebox.showinfo('Błąd', 'Odbiorca nie zaakceptował połączenia.')
            self.return_to_main_frame()

    # Runs timer
    def refresh_timer(self, number):
        # If timer still has > seconds left decrement the number and continue counting
        if number != -1 \
                and not self.controller.shared_data["waiting_frame"]["stop_timer_flag"] \
                and not self.controller.shared_data["waiting_frame"]["not_accepted_flag"]:
            self.timer.configure(text=number)
            self.timer.after(1000, self.refresh_timer, number-1)
        # If timer was stopped by another function (ie. user accepted connection) - stop counting
        elif self.controller.shared_data["waiting_frame"]["stop_timer_flag"]:
            self.stop_timer()
            return
        # That means timer has run out of time, show not accepted message and set flag
        elif self.controller.shared_data["waiting_frame"]["not_accepted_flag"]:
            self.after(10, self.show_not_accepted_message)
        else:
            self.controller.shared_data["waiting_frame"]["not_accepted_flag"] = True
            self.after(10, self.show_not_accepted_message)

    # Run when displaying frame
    def on_show(self, event):
        # Try will fail for the first time and exception AttributeError will cover first run of this frame
        try:
            # Refresh receiver label containing IP address of receiver
            self.receiver_label.pack_forget()
            receiver_label_text = "Oczekiwanie na {}".format(self.controller.shared_data["host_ip"])
            self.receiver_label.configure(text=receiver_label_text)
            self.receiver_label.pack(side="top")

            # Set flags
            self.controller.shared_data["waiting_frame"]["not_accepted_flag"] = False
            self.controller.shared_data["waiting_frame"]["stop_timer_flag"] = False

            # Pack and run timer
            self.timer.pack()
            self.timer.after(0, self.refresh_timer, 30)
        except AttributeError:
            # Display receiver label
            receiver_label_text = "Oczekiwanie na {}".format(self.controller.shared_data["host_ip"])

            # Configure and display labels
            self.receiver_label.configure(text=receiver_label_text)
            self.receiver_label.pack(side="top")
            self.timer.pack()

            # Set initial flags to False
            self.controller.shared_data["waiting_frame"]["not_accepted_flag"] = False
            self.controller.shared_data["waiting_frame"]["stop_timer_flag"] = False

            # Run timer
            self.timer.after(0, self.refresh_timer, 30)

