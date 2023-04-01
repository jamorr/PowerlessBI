import tkinter as tk

# Create the tkinter window
root = tk.Tk()

# Create a function to add a button to the first empty row
def add_button():
    # Get the number of rows in the grid
    rows = root.grid_size()[1]

    # Add a button to the first empty row
    button = tk.Button(root, text="Delete row", command=delete_row)
    button.grid(row=rows, column=0)

    # Add 5 labels to row 0 in columns 1-5
    for i in range(1, 6):
        label = tk.Label(root, text=f"Label {i}")
        label.grid(row=0, column=i)

# Create a function to delete objects in the same row as the button
def delete_row():
    # Get the row and column of the button
    row = int(root.focus_get().grid_info()["row"])
    column = int(root.focus_get().grid_info()["column"])

    # Delete objects in the same row as the button
    for i in range(6):
        root.grid_slaves(row=row, column=i)[0].destroy()

# Add the button to the window
add_button()

# Start the main event loop
root.mainloop()
