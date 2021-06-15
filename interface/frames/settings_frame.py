import tkinter as tk
import re


class SettingsFrame(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self["bg"] = '#a3d4c5'

        self.controller = controller
        return_button = tk.Button(self, text="Wróć do poprzedniej strony", command=self.controller.return_to_main_frame)
        return_button.pack(side="bottom")

        self.controller.modulation_var = tk.IntVar()

        self.modulation_scale = tk.Scale(self, orient="horizontal", background="#a3d4c5", from_=-5, to=5)
        self.modulation_scale.pack()
        modulation_button = tk.Button(self, text="Ustaw", background="#a3d4c5", command=self.set_modulation_value)
        modulation_button.pack()

        self.modulation_label = tk.Label(self, text="Wartosc modulacji: {}".format(self.modulation_scale.get()), background="#a3d4c5")
        self.modulation_label.pack()

        self.bind("<<ShowFrame>>", self.on_show)

    def on_show(self, event):
        pass

    def set_modulation_value(self):
        self.controller.shared_data["modulation_value"] = self.modulation_scale.get()
        self.modulation_label.configure(text="Wartosc modulacji: {}".format(self.modulation_scale.get()))