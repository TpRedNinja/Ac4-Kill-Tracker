import pymem
import tkinter as tk
from tkinter import ttk
import json

def test_process_connection(process_name):
    try:
        pm = pymem.Pymem(process_name)
        return pm
    except Exception as e:
        return None

def connect_to_game(process_name):
    pm = test_process_connection(process_name)
    if pm:
        return pm
    else:
        return None

def read_pointer(pm, base_address, offsets):
    try:
        address = pm.read_uint(base_address)
        for offset in offsets[:-1]:
            address = pm.read_uint(address + offset)
        final_address = address + offsets[-1]
        return pm.read_int(final_address)
    except pymem.exception.MemoryReadError as e:
        return None

def read_pointer_from_file():
    try:
        with open('pointer.json', 'r') as f:
            data = json.load(f)
        base_address = int(data['base_address'], 16)
        offsets = [int(offset, 16) for offset in data['offsets']]
        return base_address, offsets
    except FileNotFoundError:
        print("pointer.json not found. Please create it with the correct pointer information.")
        return None, None

def write_kills_to_file(kills_value):
    with open('totalkills.txt', 'w') as f:
        f.write(str(kills_value))

class GameGUI:
    def __init__(self, master):
        self.master = master
        master.title("Assassin's Creed 4 Kill Tracker")
        master.configure(bg='black')

        self.game_options = ["", "Assassin's Creed 4", "Assassin's Creed Syndicate"]
        self.selected_game = tk.StringVar()
        self.selected_game.set(self.game_options[0])

        self.game_dropdown = ttk.Combobox(master, textvariable=self.selected_game, values=self.game_options)
        self.game_dropdown.pack(pady=10)

        self.connect_button = tk.Button(master, text="Connect to Game", command=self.connect_to_game, bg='gray', fg='white')
        self.connect_button.pack(pady=5)

        self.disconnect_button = tk.Button(master, text="Disconnect", command=self.disconnect_from_game, bg='gray', fg='white', state=tk.DISABLED)
        self.disconnect_button.pack(pady=5)

        self.connection_label = tk.Label(master, text="Not connected", bg='black', fg='white')
        self.connection_label.pack(pady=5)

        self.kills_label = tk.Label(master, text="Total Kills: N/A", bg='black', fg='white')
        self.kills_label.pack(pady=5)

        self.pointer_label = tk.Label(master, text="Current Pointer: N/A", bg='black', fg='white')
        self.pointer_label.pack(pady=5)

        self.pm = None
        self.current_process = None
        self.update_loop = None

        self.base_address, self.offsets = read_pointer_from_file()
        self.update_pointer_label()

    def update_pointer_label(self):
        if self.base_address is not None and self.offsets is not None:
            offset_str = ", ".join([f"+{hex(offset)}" for offset in self.offsets])
            self.pointer_label.config(text=f"Current Pointer: Base+{hex(self.base_address)}, {offset_str}")
        else:
            self.pointer_label.config(text="Current Pointer: Invalid pointer information")

    def connect_to_game(self):
        selected_game = self.selected_game.get()
        if selected_game == "Assassin's Creed 4":
            self.current_process = "AC4BFSP.exe"
        elif selected_game == "Assassin's Creed Syndicate":
            self.current_process = "ACS.exe"
        else:
            self.connection_label.config(text="Please select a game.")
            return

        self.pm = connect_to_game(self.current_process)
        if self.pm:
            self.connection_label.config(text=f"Connected to {selected_game}")
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.start_update_loop()
            self.update_pointer_label()
        else:
            self.connection_label.config(text="Error: Cannot connect to process. Make sure the game is running.")

    def disconnect_from_game(self):
        if self.update_loop:
            self.master.after_cancel(self.update_loop)
            self.update_loop = None
        self.pm = None
        self.current_process = None
        self.connection_label.config(text="Disconnected")
        self.kills_label.config(text="Total Kills: N/A")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)

    def start_update_loop(self):
        self.update_kills()
        self.update_loop = self.master.after(1000, self.start_update_loop)

    def update_kills(self):
        if self.pm and self.current_process == "AC4BFSP.exe":
            try:
                module = pymem.process.module_from_name(self.pm.process_handle, self.current_process)
                base_address = module.lpBaseOfDll + self.base_address
                kills_value = read_pointer(self.pm, base_address, self.offsets)
                
                if kills_value is not None:
                    self.kills_label.config(text=f"Total Kills: {kills_value}")
                    write_kills_to_file(kills_value)
                else:
                    self.kills_label.config(text="Failed to read total kills")
            except Exception as e:
                self.kills_label.config(text=f"Error: {e}")
        elif self.pm and self.current_process == "ACS.exe":
            self.kills_label.config(text="Kills feature not available for Assassin's Creed Syndicate")
        else:
            self.kills_label.config(text="Not connected to Assassin's Creed 4")

root = tk.Tk()
root.geometry("800x500")
gui = GameGUI(root)
root.mainloop()
