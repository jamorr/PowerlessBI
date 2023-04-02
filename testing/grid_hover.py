import tkinter as tk

def print_grid(event):
    row = event.widget.grid_info()['row']
    col = event.widget.grid_info()['column']
    print(f"Mouse is hovering over row {row}, column {col}")

root = tk.Tk()
root.geometry("500x500")

for i in range(10):
    for j in range(5):
        frame = tk.Frame(root, bg=f"#{i*25:02x}{j*50:02x}ff", width=50, height=50)
        frame.grid(row=i, column=j)
        frame.bind("<Enter>", print_grid)
        # frame.grid_propagate(False)

root.mainloop()
