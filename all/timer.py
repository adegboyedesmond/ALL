import tkinter as tk
from PIL import Image, ImageTk

# -------- SETTINGS --------
WARNING_TIME = 10
paused = False
current_time = 0
blink_state = True
display_name = ""
selected_person = None

# -------- FUNCTIONS --------

def parse_time(text):
    if ":" in text:
        mins, secs = map(int, text.split(":"))
        return mins * 60 + secs
    return int(text)

def start_timer():
    global current_time, paused, display_name
    try:
        current_time = parse_time(entry.get())
        paused = False

        # Get selected name
        if selected_person.get() == "Custom":
            display_name = custom_entry.get() or "Guest"
        else:
            display_name = selected_person.get()

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

        # Show time + person
        timer_label.config(text=f"{mins:02}:{secs:02} - {display_name}")

        if current_time <= WARNING_TIME and current_time != 0:
            blink_warning()
        else:
            warning_label.config(text="", fg="yellow")

        current_time -= 1
        root.after(1000, countdown)
    else:
        fade_to_green()
        show_end_screen()

def blink_warning():
    global blink_state
    if blink_state:
        warning_label.config(text="⚠ WARNING: Time is almost up", fg="red")
    else:
        warning_label.config(text="", fg="yellow")

    blink_state = not blink_state
    root.after(500, blink_warning)

def fade_to_green(step=0):
    if step > 20:
        return
    green_value = int(255 * (step / 20))
    color = f'#00{green_value:02x}00'
    root.configure(bg=color)
    root.after(50, fade_to_green, step + 1)

def pause_resume():
    global paused
    paused = not paused
    if not paused:
        countdown()

def reset_app(event=None):
    global paused
    paused = False
    root.configure(bg="black")
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

# -------- UI --------

root = tk.Tk()
root.title("Ultimate Timer")
root.configure(bg="black")

root.bind("<Escape>", reset_app)

# -------- INPUT SCREEN --------
input_frame = tk.Frame(root, bg="black")

entry = tk.Entry(input_frame, font=("Arial", 20), justify="center")
entry.pack(pady=20)

hint = tk.Label(
    input_frame,
    text="Enter seconds or MM:SS (e.g. 90 or 1:30)",
    fg="white",
    bg="black"
)
hint.pack()

# Dropdown
selected_person = tk.StringVar()
selected_person.set("Pastor")

options = ["Pastor", "Choir", "Praise Team", "Custom"]
dropdown = tk.OptionMenu(input_frame, selected_person, *options)
dropdown.config(font=("Arial", 14))
dropdown.pack(pady=10)

# Custom entry
custom_entry = tk.Entry(input_frame, font=("Arial", 14), justify="center")

selected_person.trace("w", check_custom)

start_btn = tk.Button(
    input_frame,
    text="Start Timer",
    font=("Arial", 14),
    command=start_timer
)
start_btn.pack(pady=10)

# -------- TIMER SCREEN --------
timer_frame = tk.Frame(root, bg="black")

timer_label = tk.Label(
    timer_frame,
    text="00:00",
    font=("Arial", 90),
    fg="white",
    bg="black"
)
timer_label.pack(expand=True)

warning_label = tk.Label(
    timer_frame,
    text="",
    font=("Arial", 30),
    bg="black"
)
warning_label.pack()

controls = tk.Frame(timer_frame, bg="black")
controls.pack(pady=20)

tk.Button(controls, text="Pause/Resume", command=pause_resume).pack(side="left", padx=10)
tk.Button(controls, text="Reset", command=reset_app).pack(side="left", padx=10)

# -------- END SCREEN --------
end_frame = tk.Frame(root, bg="red")

end_label = tk.Label(
    end_frame,
    text="TIME's UP",
    font=("Arial", 80),
    fg="white",
    bg="red"
)
end_label.pack(pady=20)

# Image or fallback drawing
try:
    img = Image.open("stop.png")
    img = img.resize((300, 300))
    img = ImageTk.PhotoImage(img)

    img_label = tk.Label(end_frame, image=img, bg="red")
    img_label.pack()
except:
    canvas = tk.Canvas(
        end_frame,
        width=300,
        height=200,
        bg="red",
        highlightthickness=0
    )
    canvas.pack()

    canvas.create_oval(130, 20, 170, 60, fill="black")
    canvas.create_line(150, 60, 150, 120, width=3)
    canvas.create_line(150, 80, 110, 100, width=3)
    canvas.create_line(150, 80, 190, 100, width=3)
    canvas.create_line(150, 120, 120, 160, width=3)
    canvas.create_line(150, 120, 180, 160, width=3)

    canvas.create_rectangle(190, 90, 240, 140, fill="red")
    canvas.create_text(215, 115, text="STOP", fill="white")

# -------- START --------
show_input_screen()
root.mainloop()