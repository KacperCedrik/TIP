import threading
import socket
import pyaudio
import tkinter as tk
import numpy as np
import wave
import struct
import math
import random

from random import randint
from tkinter import messagebox

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10
WIDTH = 2


class ConnectionHandler(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.flags = [0, 0, 0]
        self.thread_stopper = {
            "listener": False,
            "clienter": False
        }
        self.listener = threading.Thread(target=self.listener_action, args=())
        self.listener.start()
        self.clienter = threading.Thread(target=self.client_action, args=())
        self.clienter.start()

        self.modulation = None

        self.GLOBAL_IP = self.get_local_ip()

    def add_source_and_target_to_conversation(self, source, target):
        actual_conversation = self.controller.get_current_conversation()
        actual_conversation["source"] = source
        actual_conversation["target"] = target

    def update_messages_sent(self):
        actual_conversation = self.controller.get_current_conversation()

        if actual_conversation["messages-sent"] is None:
            actual_conversation["messages-sent"] = 0
            actual_conversation["messages-sent"] = actual_conversation["messages-sent"] + 1
        else:
            actual_conversation["messages-sent"] = actual_conversation["messages-sent"] + 1

    def update_messages_sent_by_source(self):
        actual_conversation = self.controller.get_current_conversation()

        if actual_conversation["messages-sent-by-source"] is None:
            actual_conversation["messages-sent-by-source"] = 0
            actual_conversation["messages-sent-by-source"] = actual_conversation["messages-sent-by-source"] + 1
        else:
            actual_conversation["messages-sent-by-source"] = actual_conversation["messages-sent-by-source"] + 1

    def update_messages_sent_by_target(self):
        actual_conversation = self.controller.get_current_conversation()

        if actual_conversation["messages-sent-by-target"] is None:
            actual_conversation["messages-sent-by-target"] = 0
            actual_conversation["messages-sent-by-target"] = actual_conversation["messages-sent-by-target"] + 1
        else:
            actual_conversation["messages-sent-by-target"] = actual_conversation["messages-sent-by-target"] + 1

    def modulate_voice(self, data):
        width = 2
        data = np.array(wave.struct.unpack("%dh" % (len(data) / width), data)) * 2

        data = np.fft.rfft(data)

        data2 = [0] * len(data)
        if self.modulation >= 0:
            data2[self.modulation:len(data)] = data[0:(len(data) - self.modulation)]
            data2[0:self.modulation] = data[(len(data) - self.modulation):len(data)]
        else:
            data2[0:(len(data) + self.modulation)] = data[-self.modulation:len(data)]
            data2[(len(data) + self.modulation):len(data)] = data[0:-self.modulation]

        data = np.array(data2)

        data = np.fft.irfft(data)

        data_out = np.array(data * 0.5, dtype='int16')  # undo the *2 that was done at reading
        chunk_out = struct.pack("%dh" % (len(data_out)), *list(data_out))  # convert back to 16-bit data
        return chunk_out

    def listener_action(self):
        proto = socket.getprotobyname('tcp')
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)
        # self.listen_port = randint(20000, 21000)
        self.listen_port = 22222
        print("Slucham na porcie {}".format(self.listen_port))
        self.listener_socket.bind((self.get_local_ip(), self.listen_port))
        self.listener_socket.listen(1)
        try:
            while 1:
                conn, addr = self.listener_socket.accept()
                message = self.utf_to_str(str(conn.recv(3)))
                # tk.messagebox.showinfo("Informacja", "listenAction: Nowa rozmowa typu: {}".format(str(message)))
                if message == "EXI":  # komunikat pobudzający, nie oczekuje odpowiedzi
                    conn.close()
                    break
                elif message == "CON":
                    if self.is_busy():  # is busy
                        new_message = "NAK".encode('utf-8')
                        conn.send(new_message)
                        pass
                    else:
                        self.i_am_busy()
                        if tk.messagebox.askokcancel("{} - akcja".format(self.GLOBAL_IP),
                                                     "Połączenie przychodzące od {}"
                                                     "- czy chcesz odebrać?".format(addr[0])):
                            new_message = "ACK".encode('utf-8')
                            conn.send(new_message)

                            self.controller.shared_data["who_called"] = "you"
                            self.controller.show_frame("ConversationFrame")
                            self.add_source_and_target_to_conversation(str(self.get_local_ip()), addr[0])
                            self.conversation_listener(conn)

                        else:
                            new_message = "NAK".encode('utf-8')
                            conn.send(new_message)
                elif self.thread_stopper["listener"]:
                    self.listener_socket.close()
                    break
        except OSError:
            tk.messagebox.showinfo("Blad", "Rozmowca niepoprawnie zakonczyl polaczenie")
            self.controller.close_conversation_frame()
            print("Closed listener socket")

    def conversation_listener(self, conn):
        # GENEROWANIE PARAMETRÓW
        p, q = self.los_pq()
        n = p * q
        phi = (p - 1) * (q - 1)
        e = self.gen_e(phi)
        d = self.gen_d(phi, e)

        # public_key = [e, n]  # Wysyłaj komu chcesz, on będzie dla ciebie tym szyfrował
        # private_key = [d, n]  # Nie wysyłaj

        # Wymiana kluczy publicznych
        e2 = conn.recv(8)
        e2 = int(e2)

        sep = ''
        val = str(e) + sep
        conn.send(val.encode('utf-8'))

        n2 = conn.recv(8)
        n2 = int(n2)

        val = str(n) + sep
        conn.send(val.encode('utf-8'))

        while 1:
            self.controller.shared_data["cycle_ender"] = "new_cycle"
            # print("Czekam na komunikat")
            self.modulation = self.controller.shared_data["modulation_value"]

            message = conn.recv(12)
            message = self.asr(self.utf_to_str(str(message)), d, n)

            if message == "END":
                # print("Druga strona zażądała zakończenia rozmowy")
                if tk.messagebox.askokcancel("{} - akcja".format(self.GLOBAL_IP),
                                             "Kolega zażądał zakończenia rozmowy. Zgódź się (Ok), bądź odrzuć (Anuluj)."):

                    # Zgoda, komunikat do drugiej strony
                    message = self.rsa("ACK", e2, n2)
                    conn.send(message.encode('utf-8'))

                else:
                    # Nie zgoda, komunikat do drugiej strony
                    message = self.rsa("NAK", e2, n2)
                    conn.send(message.encode('utf-8'))

                    self.controller.shared_data["cycle_ender"] = "new_cycle"
                    # Nagrywanie
                    p = pyaudio.PyAudio()
                    stream = p.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    input=True,
                                    frames_per_buffer=CHUNK)

                    # print("Nagrywanie: ")
                    frames = []

                    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                        data = stream.read(CHUNK)
                        data = self.modulate_voice(data)
                        frames.append(data)
                    # print("KONIEC NAGRYWANIA")

                    # Wysyłanie dźwięku
                    # print("Wysyłanie dźwięku: ")
                    for i in range(len(frames)):
                        conn.send(frames[i])

                    conn.send("KKK".encode('utf-8'))  # Znacznik EOM

                    # Zamknięcie strumieni dźwiękowych
                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                # Niezależnie od wersji, teraz zakończ połączenie
                self.controller.close_conversation_frame()
                self.i_am_free()
                break
            elif message == "NED":
                # ustawienia dla odbierania i wysyłania

                # Odbieranie dźwięku
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(WIDTH),
                                channels=CHANNELS,
                                rate=RATE,
                                output=True,
                                frames_per_buffer=CHUNK)

                # print("Odbieranie dźwięku")
                self.update_messages_sent()
                self.update_messages_sent_by_source()
                frames = []
                while 1:
                    data = conn.recv(1024)
                    if str(data)[len(str(data)) - 2] == "K" \
                            and str(data)[len(str(data)) - 3] == "K" \
                            and str(data)[len(str(data)) - 4] == "K":
                        # print("Znaleziono K")
                        break
                    frames.append(data)

                # print("Odtworzenie")
                for x in range(len(frames)):
                    stream.write(frames[x])

                # print("Zamknięcie strumieni dźwiękowych")
                stream.stop_stream()
                stream.close()
                p.terminate()

                # Koniec / nagraj
                if not tk.messagebox.askokcancel("{} - akcja".format(self.GLOBAL_IP),
                                                 "Co chcesz zrobić? Kontynuuj rozmowę (Ok), bądź odrzuć (Anuluj)."):

                    # Komunikat do drugiej strony

                    message = self.rsa("END", e2, n2)
                    conn.send(message.encode('utf-8'))

                    # czekam na zgodę zakończenia

                    message = conn.recv(12)
                    message = self.asr(self.utf_to_str(str(message)), d, n)

                    # nie zgoda, czekam na ostatnią wiadomość
                    if message == "NAK":
                        # Odbieranie dźwięku
                        p = pyaudio.PyAudio()
                        stream = p.open(format=p.get_format_from_width(WIDTH),
                                        channels=CHANNELS,
                                        rate=RATE,
                                        output=True,
                                        frames_per_buffer=CHUNK)

                        self.update_messages_sent()
                        self.update_messages_sent_by_source()

                        # print("Odbieranie dźwięku")
                        frames = []
                        while 1:
                            data = conn.recv(1024)
                            if str(data)[len(str(data)) - 2] == "K" \
                                    and str(data)[len(str(data)) - 3] == "K" \
                                    and str(data)[len(str(data)) - 4] == "K":
                                # print("Znaleziono K")
                                break
                            frames.append(data)

                        # print("Odtworzenie")
                        for x in range(len(frames)):
                            stream.write(frames[x])

                        stream.stop_stream()
                        stream.close()
                        p.terminate()

                    # W obu przypadkach teraz zakończ rozmowę
                    self.controller.close_conversation_frame()
                    self.i_am_free()
                    break

                else:
                    self.controller.shared_data["cycle_ender"] = "new_cycle"

                    p = pyaudio.PyAudio()
                    stream = p.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    input=True,
                                    frames_per_buffer=CHUNK)

                    # Nagrywanie
                    # print("Nagrywanie: ")
                    frames = []

                    self.update_messages_sent()
                    self.update_messages_sent_by_target()

                    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                        data = stream.read(CHUNK)
                        data = self.modulate_voice(data)
                        frames.append(data)
                    # print("KONIEC NAGRYWANIA")

                    # Wysyłanie komunikatu
                    message = self.rsa("NED", e2, n2)
                    conn.send(message.encode('utf-8'))

                    # Wysyłanie dźwięku
                    # print("Wysyłanie dźwięku: ")
                    for i in range(len(frames)):
                        conn.send(frames[i])

                    conn.send("KKK".encode('utf-8'))

                    # Zamknięcie strumieni dźwiękowych
                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                    # print("Zakończenie wysyłania. Czekam na odpowiedź wroga")
            elif self.thread_stopper["listener"]:
                conn.close()
                break
            else:
                tk.messagebox.showinfo("Blad", "Wadliwy komunikat: listenAction [ KONIEC / NIE KONIEC ]")


    def client_action(self):
        while 1:
            proto = socket.getprotobyname('tcp')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)
            if self.is_free() and self.controller.shared_data["host_ip"] != "":
                self.i_am_busy()
                adres = self.controller.shared_data["host_ip"]
                # port = self.controller.shared_data["host_port"]
                port = 22222
                # print("Łączę z adresem: " + str(adres))
                try:
                    s.connect((adres, int(port)))

                    # Żądanie rozmowy
                    message = "CON".encode('utf-8')
                    s.send(message)

                    while not self.controller.shared_data["waiting_frame"]["not_accepted_flag"]:
                        resp = self.utf_to_str(str(s.recv(1024)))
                        if resp != "":
                            # print("A oto odpowiedź: " + resp)
                            break
                    if resp != "ACK":
                        # print("Ta osoba X nie ma teraz czasu na rozmowę!")
                        self.controller.shared_data["waiting_frame"]["not_accepted_flag"] = True
                        pass  # finally zamknie sockety i ustawi iAmFree
                    else:  # czyli koniecznie resp == "ACK"
                        self.controller.shared_data["waiting_frame"]["stop_timer_flag"] = True
                        # print("ZGODA na rozmowę!")

                        self.controller.shared_data["who_called"] = "me"
                        self.controller.show_frame("ConversationFrame")
                        self.add_source_and_target_to_conversation(str(self.get_local_ip()), adres)
                        self.conversation_clienter(s)

                except socket.error:
                    self.controller.shared_data["waiting_frame"]["not_accepted_flag"] = True
                    # print("Ta osoba nie ma teraz czasu na rozmowę!")
                finally:
                    self.i_am_free()
                    self.controller.shared_data["host_ip"] = ""
            elif self.thread_stopper["clienter"]:
                break


    def conversation_clienter(self, conn):

        # GENEROWANIE PARAMETRÓW
        p, q = self.los_pq()
        n = p * q
        phi = (p - 1) * (q - 1)
        e = self.gen_e(phi)
        d = self.gen_d(phi, e)

        # private_key = [d, n]  # Nie wysyłaj
        # public_key = [e, n]  # Wysyłaj komu chcesz, on będzie dla ciebie tym szyfrował

        # Wymiana kluczy
        sep = ''
        val = str(e) + sep
        conn.send(val.encode('utf-8'))

        e2 = conn.recv(8)
        e2 = int(e2)

        val = str(n) + sep
        conn.send(val.encode('utf-8'))

        n2 = conn.recv(8)
        n2 = int(n2)

        while 1:
            # print("Co chcesz zrobić: Nagraj wiadomość / Zakończ? [N/Z]")
            self.modulation = self.controller.shared_data["modulation_value"]

            if not tk.messagebox.askokcancel("{} - akcja".format(self.GLOBAL_IP),
                                             "Co chcesz zrobić? Kontynuuj rozmowę (Ok), bądź odrzuć (Anuluj)."):

                # Komunikat do drugiej strony

                message = self.rsa("END", e2, n2)
                conn.send(message.encode('utf-8'))

                # print("Wysłano komunikat")

                # czekam na zgodę zakończenia

                message = conn.recv(12)
                message = self.asr(self.utf_to_str(str(message)), d, n)

                # Nie zgoda, czekam na ostatnią wiadomość
                if message == "NAK":
                    # Odbieranie dźwięku
                    p = pyaudio.PyAudio()
                    stream = p.open(format=p.get_format_from_width(WIDTH),
                                    channels=CHANNELS,
                                    rate=RATE,
                                    output=True,
                                    frames_per_buffer=CHUNK)

                    # print("Odbieranie dźwięku")
                    frames = []

                    self.update_messages_sent()
                    self.update_messages_sent_by_target()

                    while 1:
                        data = conn.recv(1024)
                        if str(data)[len(str(data)) - 2] == "K" \
                                and str(data)[len(str(data)) - 3] == "K" \
                                and str(data)[len(str(data)) - 4] == "K":
                            # print("Znaleziono K")
                            break
                        frames.append(data)

                    # print("Odtworzenie")
                    for x in range(len(frames)):
                        stream.write(frames[x])

                    # print("Zamknięcie strumieni dźwiękowych")
                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                # W obu przypadkach teraz zakończ rozmowę
                self.controller.close_conversation_frame()
                self.i_am_free()
                break
            elif self.thread_stopper["clienter"]:
                break
            else:
                self.controller.shared_data["cycle_ender"] = "new_cycle"

                # Nagrywanie
                p = pyaudio.PyAudio()
                stream = p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)

                # print("Nagrywanie: ")
                frames = []

                self.update_messages_sent()
                self.update_messages_sent_by_source()

                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    data = self.modulate_voice(data)
                    frames.append(data)
                # print("KONIEC NAGRYWANIA")

                # Wysyłanie komunikatu informującego o nie zakończeniu = nadaniu dźwięku

                message = self.rsa("NED", e2, n2)
                conn.send(message.encode('utf-8'))

                # Wysyłanie dźwięku
                # print("Wysyłanie dźwięku: ")
                for i in range(len(frames)):
                    conn.send(frames[i])
                conn.send("KKK".encode('utf-8'))

                # Zamknięcie strumieni dźwiękowych
                stream.stop_stream()
                stream.close()
                p.terminate()

                # print("Zakończenie wysyłania. Czekam na odpowiedź wroga")
                self.controller.shared_data["cycle_ender"] = "new_cycle"

                # Czekam na komunikat

                resp = conn.recv(12)
                resp = self.asr(self.utf_to_str(str(resp)), d, n)

                if resp == "END":
                    # print("Druga strona zażądała zakończenia rozmowy")
                    if tk.messagebox.askokcancel("{} - akcja".format(self.GLOBAL_IP),
                                            "Druga strona zażądała zakończenia rozmowy. Zgódź się (Ok), bądź odrzuć (Anuluj)."):

                        # Zgoda, komunikat do drugiej strony
                        message = self.rsa("ACK", e2, n2)
                        conn.send(message.encode('utf-8'))

                    else:
                        # Nie zgoda, komunikat do drugiej strony
                        message = self.rsa("NAK", e2, n2)
                        conn.send(message.encode('utf-8'))

                        self.controller.shared_data["cycle_ender"] = "new_cycle"
                        # Nagrywanie
                        p = pyaudio.PyAudio()
                        stream = p.open(format=FORMAT,
                                        channels=CHANNELS,
                                        rate=RATE,
                                        input=True,
                                        frames_per_buffer=CHUNK)

                        # print("Nagrywanie: ")
                        frames = []

                        self.update_messages_sent()
                        self.update_messages_sent_by_source()

                        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                            data = stream.read(CHUNK)
                            data = self.modulate_voice(data)
                            frames.append(data)
                        # print("KONIEC NAGRYWANIA")

                        # Wysyłanie dźwięku
                        # print("Wysyłanie dźwięku: ")
                        for i in range(len(frames)):
                            conn.send(frames[i])

                        conn.send("KKK".encode('utf-8'))  # EOM

                        # Zamknięcie strumieni dźwiękowych
                        stream.stop_stream()
                        stream.close()
                        p.terminate()

                    # Niezależnie od wersji, teraz zakończ połączenie
                    self.i_am_free()
                    self.controller.close_conversation_frame()
                    break

                elif resp == "NED":
                    # Odbieranie dźwięku
                    p = pyaudio.PyAudio()
                    stream = p.open(format=p.get_format_from_width(WIDTH),
                                    channels=CHANNELS,
                                    rate=RATE,
                                    output=True,
                                    frames_per_buffer=CHUNK)

                    # print("Odbieranie dźwięku")
                    frames = []

                    self.update_messages_sent()
                    self.update_messages_sent_by_target()

                    while 1:
                        data = conn.recv(1024)
                        if str(data)[len(str(data)) - 2] == "K" \
                                and str(data)[len(str(data)) - 3] == "K" \
                                and str(data)[len(str(data)) - 4] == "K":
                            # print("Znaleziono K")
                            break
                        frames.append(data)

                    # print("Odtworzenie")
                    for x in range(len(frames)):
                        stream.write(frames[x])

                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                else:
                    tk.messagebox.showinfo("Blad", "Wadliwy komunikat: listenAction [ KONIEC / NIE KONIEC ]")

    @staticmethod
    def get_local_ip():
        ip_address_list = socket.gethostbyname_ex(socket.gethostname())[2]

        local = "not_found"

        for address in ip_address_list:
            if address[0] == '1' and address[1] == '9' and address[2] == '2':
                local = address

        return local

    def i_am_busy(self):
        self.flags[1] = 1

    def i_am_free(self):
        self.flags[1] = 0

    def is_busy(self):
        if self.flags[1] == 0:
            return False
        return True

    def is_free(self):
        if self.flags[1] == 0:
            return True
        return False

    def exit_listener(self):
        done = False
        while not done:
            test_socket_protocol = socket.getprotobyname('tcp')  # [1]
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, test_socket_protocol)  # [2]
            try:
                test_socket.connect((self.get_local_ip(), self.listen_port))  # [3]
                message = "EXI"
                message = message.encode('utf-8')
                test_socket.send(message)  # [4]
                done = True
            except socket.error:
                print("CheckTheFlag: Złe IP!")
                pass
            finally:
                test_socket.close()

    @staticmethod
    def utf_to_str(word):
        if len(word) > 3:
            word = word[2:len(word) - 1]
        return word

    def czy_pierwsza(self, liczba):
        if liczba < 2:
            return False
        for x in range(2, int(math.sqrt(liczba)) + 1):
            if liczba % x == 0:
                return False
        return True

    def los_pq(self):
        pierwsze = []
        for x in range(10, 100):  # Tu możesz ustawić zakres
            if self.czy_pierwsza(x):
                pierwsze.append(x)

        p = random.choice(pierwsze)
        q = random.choice(pierwsze)
        return p, q

    def nwd(self, a, b):
        while b:
            a, b = b, a % b
        return a

    def gen_e(self, phi):
        i = 5  # Tu możesz DOWOLNIE ustawić wartość minimalną.
        while 1:
            if self.czy_pierwsza(i) and self.nwd(phi, i) == 1:
                return i
            i = i + 1

    def gen_d(self, phi, e):
        d = 2  # Tu możesz DOWOLNIE ustawić wartość minimalną
        # print("Otwieram wieczną pętlę")
        while 1:
            if (e * d - 1) % phi == 0:
                # print("Zamykam wieczną pętlę")
                return d
            d = d + 1

    def rsa(self, napis, e2, n2):
        wynik = 0
        for x in range(len(napis)):
            wynik = wynik + (ord(napis[x]) ** e2 % n2) * (10000 ** (len(napis) - 1 - x))
        sep = ''
        wynik = str(wynik) + sep
        return wynik

    def asr(self, liczba, d, n):  # liczba = string liczby, patrz zwracany typ metody rsa
        liczba = int(liczba)
        wynik = ""
        for x in range(3):
            wynik = str(chr((liczba % 10000) ** d % n)) + wynik
            liczba = int(liczba / 10000)

        return wynik
