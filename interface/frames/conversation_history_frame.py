import tkinter
import ast


class ConversationHistoryFrame(tkinter.Frame):

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self, parent, width=350, height=300)

        self.controller = controller
        self.bind("<<ShowFrame>>", self.on_show)

        self.pack_propagate(0)
        button = tkinter.Button(self, text="Wróć do poprzedniej strony", command=lambda: self.on_leave())
        button.pack(side=tkinter.BOTTOM)

        self.scrollbar = tkinter.Scrollbar(self)
        self.scrollbar.pack(side=tkinter.RIGHT, fill="y")

        self.mylist = tkinter.Listbox(self, yscrollcommand=self.scrollbar.set)
        self.mylist.bind("<<ListboxSelect>>", self.on_select)

    def on_leave(self):
        try:
            self.conversation_label_frame.configure(text="")
            self.on_show_message.configure(text="")
            self.mylist.delete(0,"end")
            self.controller.show_frame("IPSearchFrame")
        except AttributeError:
            self.mylist.delete(0, "end")
            self.controller.show_frame("IPSearchFrame")

    def on_select(self, event):
        try:
            selected = event.widget
            index = int(selected.curselection()[0])
            self.conversation_label_frame.configure(text=f"Konwersacja {self.conversation_history[index].get('id')}")
            self.on_show_message.configure(text=self.controller.conversationHistory.prettifyConversation(self.conversation_history[index]))
        except AttributeError:
            selected = event.widget
            index = int(selected.curselection()[0])
            self.conversation_label_frame = tkinter.LabelFrame(self, text=f"Konwersacja {self.conversation_history[index].get('id')}")
            self.conversation_label_frame.pack(fill="both", expand="yes")
            self.on_show_message = tkinter.Message(self.conversation_label_frame,
                                              text=self.controller.conversationHistory.prettifyConversation(self.conversation_history[index]))
            self.on_show_message.pack()

    def on_show(self, event):
        self.conversation_history = self.controller.conversationHistory.getConversationHistory()
        for conversation in self.conversation_history:
            self.mylist.insert(tkinter.END, "Rozmowa o ID: " + str(conversation["id"]))
            self.mylist.pack(side="left", fill=tkinter.BOTH)
            self.scrollbar.config(command=self.mylist.yview)
