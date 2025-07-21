import tkinter as tk
from tkinter import font

# Function to handle button clicks
def button_click(value):
    current = entry.get()
    entry.delete(0, tk.END)
    entry.insert(0, current + value)

# Function to evaluate the expression
def evaluate():
    try:
        result = eval(entry.get())
        entry.delete(0, tk.END)
        entry.insert(0, str(result))
    except Exception as e:
        entry.delete(0, tk.END)
        entry.insert(0, "Error")

# Function to clear the entry
def clear():
    entry.delete(0, tk.END)

# Create the main window
root = tk.Tk()
root.title("Calculator")
root.geometry("300x450")  # Set window size
root.configure(bg="#2E3440")  # Dark background color

# Custom fonts
button_font = font.Font(family="Helvetica", size=14, weight="bold")
entry_font = font.Font(family="Helvetica", size=18, weight="bold")

# Entry widget to display input and results
entry = tk.Entry(
    root,
    width=15,
    font=entry_font,
    bg="#4C566A",  # Light gray background
    fg="#ECEFF4",  # White text
    relief=tk.FLAT,
    justify=tk.RIGHT,
    bd=0,
)
entry.pack(pady=20, padx=20, ipady=10)

# Button layout
buttons = [
    ("7", "#81A1C1"), ("8", "#81A1C1"), ("9", "#81A1C1"), ("/", "#D08770"),
    ("4", "#81A1C1"), ("5", "#81A1C1"), ("6", "#81A1C1"), ("*", "#D08770"),
    ("1", "#81A1C1"), ("2", "#81A1C1"), ("3", "#81A1C1"), ("-", "#D08770"),
    ("0", "#81A1C1"), (".", "#81A1C1"), ("C", "#BF616A"), ("+", "#D08770"),
    ("=", "#A3BE8C")
]

# Frame to hold buttons
button_frame = tk.Frame(root, bg="#2E3440")
button_frame.pack(pady=10)

# Add buttons to the frame
for i, (text, color) in enumerate(buttons):
    button = tk.Button(
        button_frame,
        text=text,
        font=button_font,
        bg=color,
        fg="#2E3440",  # Dark text
        relief=tk.FLAT,
        bd=0,
        padx=20,
        pady=10,
        command=lambda t=text: button_click(t) if t not in {"=", "C"} else evaluate() if t == "=" else clear(),
    )
    button.grid(row=i // 4, column=i % 4, padx=5, pady=5)

# Run the app
root.mainloop()