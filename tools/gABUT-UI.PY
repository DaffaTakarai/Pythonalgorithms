#!/usr/bin/env python3
"""
gabut_gui.py — versi GUI dari gabut.py
Menggunakan CustomTkinter (dark mode, rounded buttons).
"""

import random
import time
import threading
import customtkinter as ctk
from tkinter import messagebox

# ========================
# DATA
# ========================

JOKES = [
    "Kenapa programmer suka kopi? Karena tanpa kopi, mereka nggak bisa 'compile' pagi hari.",
    "Ada dua jenis orang di dunia: yang ngerti biner dan yang nggak. (01000010)",
    "Kenapa buku matematika sedih? Karena isinya banyak masalah.",
    "Saya ingin jadi programmer yang sabar. Sekarang saya debug sambil nangis pelan-pelan."
]

QUOTES = [
    "Kerja keras, tapi jangan lupa istirahat. — gabut.py",
    "Buat yang lagi gabut: sedikit istirahat bisa bikin ide besar muncul.",
    "Tidak apa-apa tidak produktif kadang-kadang. Recharge dulu."
]

ASCII_ART = [
    "(\\_/)\n( •_•)\n/ >🍪   — Nyalakan mode ngemil!",
    "|\\_/|\n(o o)  — Kucing gabut menatapmu.\n=\\ /=",
    "(\\__/)\n(•ㅅ•)  ||  — Peluk virtual incoming\n/ 　 づ"
]

PROCRAST_TASKS = [
    "Susun 3 ide proyek random (cukup tulis judulnya).",
    "Bersihkan desktop dari file yang tidak perlu selama 3 menit.",
    "Tulis pesan singkat 'Hai' ke teman lama.",
    "Buat playlist 5 lagu yang bikin semangat.",
    "Buka foto lama dan pilih 1 yang bikin kamu senyum."
]

# ========================
# FUNGSI UTAMA
# ========================

def show_result(text):
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", text)
    output_box.configure(state="disabled")

def show_joke():
    show_result(random.choice(JOKES))

def show_quote():
    show_result(random.choice(QUOTES))

def show_ascii():
    show_result(random.choice(ASCII_ART))

def show_task():
    show_result(random.choice(PROCRAST_TASKS))

def guess_number():
    target = random.randint(1, 50)
    for _ in range(6):
        guess = ctk.CTkInputDialog(text="Tebak angka (1-50):", title="Mini Game").get_input()
        if not guess:
            return
        try:
            guess = int(guess)
        except ValueError:
            messagebox.showinfo("Oops", "Masukkan angka yang valid.")
            continue
        if guess == target:
            messagebox.showinfo("🎉", "Tebakanmu benar!")
            return
        elif guess < target:
            messagebox.showinfo("Petunjuk", "Terlalu kecil.")
        else:
            messagebox.showinfo("Petunjuk", "Terlalu besar.")
    messagebox.showinfo("Yah 😅", f"Kesempatan habis. Angkanya: {target}")

def rps_game():
    options = ["batu", "gunting", "kertas"]
    user = ctk.CTkInputDialog(text="Pilih: batu / gunting / kertas", title="Suit").get_input()
    if not user:
        return
    user = user.lower().strip()
    if user not in options:
        messagebox.showinfo("Error", "Pilihan tidak valid.")
        return
    comp = random.choice(options)
    if user == comp:
        result = f"Kamu pilih {user}, komputer pilih {comp}.\nSeri!"
    elif (user == "batu" and comp == "gunting") or (user == "gunting" and comp == "kertas") or (user == "kertas" and comp == "batu"):
        result = f"Kamu pilih {user}, komputer pilih {comp}.\nKamu menang 🎉"
    else:
        result = f"Kamu pilih {user}, komputer pilih {comp}.\nKamu kalah 😅"
    show_result(result)

def pomodoro():
    def run():
        for cycle in range(1, 4):
            show_result(f"🍅 Pomodoro ke-{cycle}: Fokus 5 menit!")
            time.sleep(5 * 60)
            show_result("🧘‍♂️ Istirahat 1 menit...")
            time.sleep(60)
        show_result("✅ Selesai! Waktunya stretch & minum air.")
    threading.Thread(target=run, daemon=True).start()
    show_result("Pomodoro dimulai (5 menit fokus / 1 menit istirahat)...")

# ========================
# GUI SETUP
# ========================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("🌙 Gabut GUI — versi CustomTkinter")
app.geometry("620x480")

title_label = ctk.CTkLabel(app, text="🌙 GABUT GUI", font=("Poppins", 24, "bold"))
title_label.pack(pady=20)

button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=10)

buttons = [
    ("🎭 Lelucon", show_joke),
    ("💭 Quote", show_quote),
    ("🐰 ASCII Art", show_ascii),
    ("🎮 Tebak Angka", guess_number),
    ("✂️ Suit", rps_game),
    ("⏱️ Pomodoro", pomodoro),
    ("🌀 Random Task", show_task),
]

for text, cmd in buttons:
    btn = ctk.CTkButton(button_frame, text=text, command=cmd, width=160, height=40, corner_radius=10)
    btn.pack(side="left", padx=6, pady=6)

output_box = ctk.CTkTextbox(app, height=220, width=560, font=("Consolas", 14))
output_box.pack(pady=10)
output_box.insert("1.0", "Selamat datang di GABUT GUI 🌙\nKlik tombol di atas untuk mulai.")
output_box.configure(state="disabled")

app.mainloop()
