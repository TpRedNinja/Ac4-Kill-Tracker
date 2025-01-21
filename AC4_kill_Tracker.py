import pymem
import tkinter as tk
from tkinter import ttk

def test_process_connection(process_name):
    try:
        pm = pymem.Pymem(process_name)
        print(f"Successfully connected to {process_name}")
        return pm
    except Exception as e:
        print(f"Failed to connect to {process_name}: {e}")
        return None

def connect_to_game(process_name):
    pm = test_process_connection(process_name)
    if pm:
        print("Game process is open and accessible.")
        return pm
    else:
        print("Failed to connect to the game.")
        return None

def read_pointer(pm, base_address, offset1, offset2):
    """
    Reads memory value using a base address and two offsets.
    """
    try:
        address = pm.read_uint(base_address)  # Read the pointer at the base address
        print(f"Address without first offset: {hex(address)}")  # Print address before applying the first offset
        
        address = pm.read_uint(address + offset1)  # Apply the first offset and read the new address
        print(f"Address with first offset applied: {hex(address)}")  # Print address after applying the first offset
        
        final_address = address + offset2  # Apply the second offset
        print(f"Address with second offset applied: {hex(final_address)}")  # Print address after applying the second offset

        return pm.read_int(final_address)  # Read the final value
    except pymem.exception.MemoryReadError as e:
        print(f"MemoryReadError: {e}")
        return None


class GameGUI:
    def __init__(self, master):
        self.master = master
        master.title("Assassins's Creed 4 kill tracker")
        master.configure(bg='black')

        self.game_options = ["", "Assassin's Creed 4", "Assassin's Creed Syndicate"]
        self.selected_game = tk.StringVar()
        self.selected_game.set(self.game_options[0])

        self.game_dropdown = ttk.Combobox(master, textvariable=self.selected_game, values=self.game_options)
        self.game_dropdown.pack(pady=10)

        self.connect_button = tk.Button(master, text="Connect to Game", command=self.connect_to_game, bg='gray', fg='white')
        self.connect_button.pack(pady=5)

        self.connection_label = tk.Label(master, text="Not connected", bg='black', fg='white')
        self.connection_label.pack(pady=5)

        self.kills_button = tk.Button(master, text="Total Kills", command=self.show_kills, bg='gray', fg='white')
        self.kills_button.pack(pady=5)

        self.kills_label = tk.Label(master, text="", bg='black', fg='white')
        self.kills_label.pack(pady=5)

        self.pm = None
        self.current_process = None

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
        else:
            self.connection_label.config(text="Error: Cannot connect to process. Make sure the game is running.")

    def show_kills(self):
        if self.pm and self.current_process == "AC4BFSP.exe":
            try:
                # Base address and offsets
                module = pymem.process.module_from_name(self.pm.process_handle, self.current_process)
                base_address = module.lpBaseOfDll + 0x01798904  # Base address + static offset
                offset1 = 0x338
                offset2 = 0x4

                print(f"Base Address: {hex(base_address)}")  # Print base address

                # Read pointer value
                kills_value = read_pointer(self.pm, base_address, offset1, offset2)
                
                if kills_value is not None:
                    self.kills_label.config(text=f"Total Kills: {kills_value}")
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
