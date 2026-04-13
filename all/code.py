import os
import sys
import tkinter as tk
from PIL import Image, ImageTk
import pyttsx3

# -------- SETTINGS --------
WARNING_TIME = 60
paused = False
current_time = 0
original_time = 0
blink_state = True
display_name = ""
selected_person = None
next_name = ""

# -------- VOICE --------
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# -------- FORMAT TIME WORDS --------
def format_time_words(seconds):
    mins = seconds // 60
    hours = mins // 60
    mins = mins % 60

    parts = []

    if hours > 0:
        parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")

    if mins > 0:
        parts.append(f"{mins} minute" if mins == 1 else f"{mins} minutes")

    if not parts:
        return "0 minute"

    return " ".join(parts)

# -------- BEEP ALARM --------
def alarm_beep(times=3):
    if times <= 0:
        speak(f"Next: {next_name}")
        return

    try:
        import winsound
        winsound.Beep(1200, 500)
    except:
        print("\a")

    root.after(600, alarm_beep, times - 1)

# -------- FUNCTIONS --------

def parse_time(text):
    if ":" in text:
        mins, secs = map(int, text.split(":"))
        return mins * 60 + secs
    return int(text)

def start_timer():
    global current_time, paused, display_name, next_name, original_time

    try:
        current_time = parse_time(entry.get())
        original_time = current_time
        paused = False

        # Current person
        if selected_person.get() == "Custom":
            display_name = custom_entry.get() or "Guest"
        else:
            display_name = selected_person.get()

        # Next program
        next_name = next_entry.get() or "Next Program"

        show_timer_screen()
        countdown()

    except:
        entry.delete(0, tk.END)
        entry.insert(0, "Use 60 or 1:00")

def countdown():
    global current_time

    if paused:
        return

    if current_time >= 0:
        mins, secs = divmod(current_time, 60)

        # MAIN TIMER
        timer_label.config(text=f"{mins:02}:{secs:02} - {display_name}")

        # GIVEN TIME (WORDS)
        given_label.config(text=f"GIVEN: {format_time_words(original_time)}")

        # WARNING
        if current_time <= WARNING_TIME and current_time != 0:
            blink_warning()
            next_program_label.config(text=f"👉 NEXT PROGRAM: {next_name}")
        else:
            warning_label.config(text="")
            next_program_label.config(text="")

        current_time -= 1
        root.after(1000, countdown)

    else:
        end_sequence()

def end_sequence():
    warning_label.config(text="")
    next_program_label.config(text="")
    timer_label.config(text="TIME'S UP")

    alarm_beep(3)  # 🔊 3 beeps then voice
    show_end_screen()

def blink_warning():
    global blink_state
    if blink_state:
        warning_label.config(text="⚠ WARNING: Time's almost up", fg="red")
    else:
        warning_label.config(text="")

    blink_state = not blink_state
    root.after(500, blink_warning)

def pause_resume():
    global paused
    paused = not paused
    if not paused:
        countdown()

def reset_app(event=None):
    global paused
    paused = False
    root.configure(bg="black")
    warning_label.config(text="")
    next_program_label.config(text="")
    given_label.config(text="")
    show_input_screen()

def show_input_screen():
    root.attributes("-fullscreen", False)
    timer_frame.pack_forget()
    end_frame.pack_forget()
    input_frame.pack(expand=True)

def show_timer_screen():
    root.attributes("-fullscreen", True)
    input_frame.pack_forget()
    end_frame.pack_forget()
    timer_frame.pack(expand=True, fill="both")

def show_end_screen():
    timer_frame.pack_forget()
    input_frame.pack_forget()
    end_frame.pack(expand=True, fill="both")

def check_custom(*args):
    if selected_person.get() == "Custom":
        custom_entry.pack(pady=5)
    else:
        custom_entry.pack_forget()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("")
    return os.path.join(base_path, relative_path)
# -------- UI --------

root = tk.Tk()
root.title("Ultimate Timer")
root.configure(bg="black")

root.bind("<Escape>", reset_app)

# -------- INPUT SCREEN --------
input_frame = tk.Frame(root, bg="black")

entry = tk.Entry(input_frame, font=("Arial", 40), justify="center")
entry.pack(pady=20)

hint = tk.Label(input_frame,
                text="Enter seconds or MM:SS (e.g. 90 or 1:30)",
                fg="white", bg="black")
hint.pack()

# Dropdown
selected_person = tk.StringVar()
selected_person.set("Pastor")

options = ["Pastor", "Choir", "Praise Team", "Custom"]
dropdown = tk.OptionMenu(input_frame, selected_person, *options)
dropdown.config(font=("Arial", 40))
dropdown.pack(pady=10)

custom_entry = tk.Entry(input_frame, font=("Arial", 30), justify="center")
selected_person.trace("w", check_custom)

# NEXT PROGRAM
next_label = tk.Label(input_frame, text="Next Program",
                      fg="white", bg="black")
next_label.pack()

next_entry = tk.Entry(input_frame, font=("Arial", 40), justify="center")
next_entry.pack(pady=5)

start_btn = tk.Button(input_frame, text="Start Timer",
                      font=("Arial", 20), command=start_timer)
start_btn.pack(pady=10)

# -------- TIMER SCREEN --------
timer_frame = tk.Frame(root, bg="black")

timer_label = tk.Label(timer_frame, text="00:00",
                       font=("Arial", 120), fg="white", bg="black")
timer_label.pack(expand=True)

warning_label = tk.Label(timer_frame, text="",
                         font=("Arial", 70), bg="black")
warning_label.pack()

next_program_label = tk.Label(timer_frame, text="",
                             font=("Arial", 60), fg="cyan", bg="black")
next_program_label.pack()

# TOP RIGHT GIVEN TIME
given_label = tk.Label(timer_frame, text="",
                       font=("Arial", 25), fg="white", bg="black")
given_label.place(relx=1, x=-20, y=20, anchor="ne")

controls = tk.Frame(timer_frame, bg="black")
controls.pack(pady=20)

tk.Button(controls, text="Pause/Resume", command=pause_resume).pack(side="left", padx=10)
tk.Button(controls, text="Reset", command=reset_app).pack(side="left", padx=10)

# -------- END SCREEN --------
end_frame = tk.Frame(root, bg="red")

end_label = tk.Label(end_frame, text="TIME'S UP",
                     font=("Arial", 100), fg="white", bg="red")
end_label.pack(pady=20)

# Image or fallback
try:
    img = Image.open(resource_path("stop.png"))
    img = img.resize((300, 300))
    img = ImageTk.PhotoImage(img)

    img_label = tk.Label(end_frame, image=img, bg="red")
    img_label.pack()
except:
    canvas = tk.Canvas(end_frame, width=300, height=200,
                       bg="red", highlightthickness=0)
    canvas.pack()
    canvas.create_oval(130, 20, 170, 60, fill="black")
    canvas.create_line(150, 60, 150, 120, width=3)
    canvas.create_line(150, 80, 110, 100, width=3)
    canvas.create_line(150, 80, 190, 100, width=3)
    canvas.create_line(150, 120, 120, 160, width=3)
    canvas.create_line(150, 120, 180, 160, width=3)
    canvas.create_rectangle(190, 90, 240, 140, fill="red")
    canvas.create_text(215, 115, text="STOP", fill="white")
show_input_screen()
root.mainloop()
