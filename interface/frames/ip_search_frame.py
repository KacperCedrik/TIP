import tkinter as tk
import re

from tkinter import messagebox


class IPSearchFrame(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self["bg"] = '#a3d4c5'

        self.controller = controller

        ip_search_message = tk.Message(self, justify="left", pady=20,
                                       bg='#a3d4c5',
                                       text="Witaj w aplikacji TIP."
                                            "\n\nW celu przeprowadzenia rozmowy "
                                            "wybierz adres IP, a nastepnie wybierz przycisk \"Połącz\".")
        ip_search_message.pack()

        ip_search_entry = tk.Entry(self, bd=10)
        ip_search_button = tk.Button(self, text="Połącz",
                                     command=lambda: self.ip_search_callback(ip_search_entry))

        ip_search_entry.pack()
        ip_search_button.pack()

        conversation_history_button = tk.Button(self, text="Historia połączeń",
                                                command=lambda: self.controller.show_frame("ConversationHistoryFrame"))
        conversation_history_button.pack()

        settings_button = tk.Button(self, text="Ustawienia",
                                    command=lambda: self.controller.show_frame("SettingsFrame"))
        settings_button.pack()

    def ip_search_callback(self, field):
        try:
            ip_search_entry_get = field.get()
            ip_regex_str = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
            port_regex_str = "^([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
#            ip, port = ip_search_entry_get.split(":")
            ip = ip_search_entry_get

            if not re.search(ip_regex_str, ip):
                raise ValueError
            # elif not re.search(port_regex_str, port):
            #     raise ValueError
        except ValueError:
            # tk.messagebox.showinfo('Tajniacy - błąd', "Należy podać poprawny adres IP "
            #                                 "wraz z portem w formacie: 0.0.0.0:1234")
            tk.messagebox.showinfo('Błąd', "Należy podać poprawny adres IP")
            return
        try:
            self.controller.shared_data["host_ip"] = ip
            # self.controller.shared_data["host_port"] = port
            self.controller.show_frame("WaitingFrame")
        except Exception as ip_search_exception:
            tk.messagebox.showinfo('Błąd', 'Nie znaleziono podanego klienta.')
            return
