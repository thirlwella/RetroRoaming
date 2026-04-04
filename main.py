#
# Retro Roaming written by Adam Thirlwell June 2021
# Update Nov 2023 - add status bar details 1.01
# Update Feb 2026 - code cleanup and robustness improvements
#
import wx
import os
import subprocess
import json
import uuid


class DataManager:
    def __init__(self):
        """Initialize the data storage location and load existing data."""
        self.datastorelocation = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "RetroRoaming")
        if not os.path.exists(self.datastorelocation):
            try:
                os.makedirs(self.datastorelocation)
            except OSError as e:
                wx.MessageBox(f"Could not create data directory: {e}", "Error", wx.OK | wx.ICON_ERROR)

        self.emu_file = os.path.join(self.datastorelocation, 'emu_data.json')
        self.game_file = os.path.join(self.datastorelocation, 'games_data.json')
        self.emu_dict = {}
        self.games_dict = {}
        self.load_data()

    def load_data(self):
        """Load emulator and game data from JSON files."""
        if os.path.isfile(self.emu_file):
            try:
                with open(self.emu_file, 'r') as ef:
                    self.emu_dict = json.load(ef)
            except (json.JSONDecodeError, IOError) as e:
                wx.MessageBox(f"Error loading emulator data: {e}", "Error", wx.OK | wx.ICON_ERROR)

        if os.path.isfile(self.game_file):
            try:
                with open(self.game_file, 'r') as gf:
                    self.games_dict = json.load(gf)
            except (json.JSONDecodeError, IOError) as e:
                wx.MessageBox(f"Error loading game data: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def save_data(self):
        """Save emulator and game data to JSON files."""
        try:
            with open(self.emu_file, 'w') as ef:
                json.dump(self.emu_dict, ef, indent=4)
            with open(self.game_file, 'w') as gf:
                json.dump(self.games_dict, gf, indent=4)
        except IOError as e:
            wx.MessageBox(f"Error saving data: {e}", "Error", wx.OK | wx.ICON_ERROR)


class MyFrame(wx.Frame):

    def __init__(self):
        super().__init__(parent=None, title='Retro Roaming', size=(1200, 800))
        self.data_manager = DataManager()
        self.emu_dict = self.data_manager.emu_dict
        self.games_dict = self.data_manager.games_dict

        panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar(1)

        # Gets a list of the emulators and picks the first one
        self.emulator_list = sorted(list(self.emu_dict.keys()))
        if self.emulator_list:
            self.emulator_name = self.emulator_list[0]
        else:
            self.emulator_name = ''

        # Sets up variables used in the program
        self.emu_executable = ''
        self.game_lib = ''
        self.current_game_id = ''
        self.default_option = ''
        self.working_directory = ''
        self.filtered_game_list = []
        self.game_index_dict = {}

        # UI Elements
        self.my_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.run_options = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.cwd = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.default_opt_ctrl = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.game_notes = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.emu_location = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.game_location = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.cmd_string = wx.TextCtrl(panel, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.cmd_string.SetForegroundColour((0, 255, 0))
        self.cmd_string.SetBackgroundColour((0, 0, 0))

        self.choice_of_emu = wx.ComboBox(panel, choices=self.emulator_list, style=wx.CB_READONLY)

        # Buttons
        play_btn = wx.Button(panel, label='Play Game', size=(100, 30))
        update_btn = wx.Button(panel, label='Update', size=(100, 30))
        exit_btn = wx.Button(panel, label='Exit', size=(100, 30))

        # Bindings
        play_btn.Bind(wx.EVT_BUTTON, self.on_run_game)
        update_btn.Bind(wx.EVT_BUTTON, self.on_update_game_details)
        exit_btn.Bind(wx.EVT_BUTTON, self.on_exit)
        self.my_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_double_click)
        self.my_list.Bind(wx.EVT_LISTBOX, self.on_list_select)
        self.choice_of_emu.Bind(wx.EVT_COMBOBOX, self.on_emulator_change)

        # Layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        main_sizer.Add(self.my_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(right_sizer, 2, wx.EXPAND | wx.ALL, 5)

        right_sizer.Add(wx.StaticText(panel, label="Emulator Selected:"), 0, wx.ALL, 5)
        right_sizer.Add(self.choice_of_emu, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Location of emulator executable:"), 0, wx.ALL, 5)
        right_sizer.Add(self.emu_location, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Working Directory:"), 0, wx.ALL, 5)
        right_sizer.Add(self.cwd, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Default Game Library Location:"), 0, wx.ALL, 5)
        right_sizer.Add(self.game_location, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Parameters passed to executable:"), 0, wx.ALL, 5)
        right_sizer.Add(self.run_options, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Default option added to new games:"), 0, wx.ALL, 5)
        right_sizer.Add(self.default_opt_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Notes on how to play:"), 0, wx.ALL, 5)
        right_sizer.Add(self.game_notes, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="This will run at command prompt:"), 0, wx.ALL, 5)
        right_sizer.Add(self.cmd_string, 0, wx.EXPAND | wx.ALL, 5)

        button_sizer.Add(play_btn, 0, wx.ALL, 5)
        button_sizer.Add(update_btn, 0, wx.ALL, 5)
        button_sizer.Add(exit_btn, 0, wx.ALL, 5)
        right_sizer.Add(button_sizer, 0, wx.CENTER)

        panel.SetSizer(main_sizer)

        # Initialize UI state
        if self.emulator_name:
            self.choice_of_emu.SetValue(self.emulator_name)
        self.filter_the_games(False)

        self.make_menu_bar()
        self.Show()

    def on_exit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def make_menu_bar(self):
        """Build the menu bar and bind event handlers."""
        file_menu = wx.Menu()
        file_open_item = file_menu.Append(-1, "&Add file location to Options\tCtrl-F",
                                         "If you want to reference a file location in options this will add it")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)

        edit_menu = wx.Menu()
        add_item = edit_menu.Append(-1, "&Add Game\tCtrl-A",
                                   "This sets up a new game record in the library")
        edit_item = edit_menu.Append(-1, "&Edit Game\tCtrl-E",
                                    "Allows you to changes details on the game in the library")
        delete_item = edit_menu.Append(-1, "&Delete Game\tCtrl-D",
                                      "Remove the game from you library")

        emu_menu = wx.Menu()
        add_emu_item = emu_menu.Append(-1, "&Add Emulator",
                                         "Add executable to start the emulator use options to pass parameters")
        edit_emu_item = emu_menu.Append(-1, "&Edit Emulator",
                                          "Edit details of the emulator set up")
        delete_emu_item = emu_menu.Append(-1, "&Delete Emulator",
                                          "Remove the emulator - this will also remove the library of games")

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT)

        menubar = wx.MenuBar()
        menubar.Append(file_menu, "&File")
        menubar.Append(edit_menu, "&Edit Game")
        menubar.Append(emu_menu, "&Edit Emulator")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        self.Bind(wx.EVT_MENU, self.on_file_open, file_open_item)
        self.Bind(wx.EVT_MENU, self.on_add_game, add_item)
        self.Bind(wx.EVT_MENU, self.on_edit_game_name, edit_item)
        self.Bind(wx.EVT_MENU, self.on_delete_game, delete_item)
        self.Bind(wx.EVT_MENU, self.on_add_emu, add_emu_item)
        self.Bind(wx.EVT_MENU, self.on_edit_emu, edit_emu_item)
        self.Bind(wx.EVT_MENU, self.on_delete_emu, delete_emu_item)

    def on_about(self, event):
        """Display an About Dialog"""
        wx.MessageBox("Retro Roaming, allowing you to run and organise your games.\n\n"
                      "Written by Adam Thirlwell (thirlwella@gmail.com)\n"
                      "Cleaned up and improved Feb 2026",
                      "About Retro Roaming",
                      wx.OK | wx.ICON_INFORMATION | wx.CENTER)

    def on_add_game(self, event):
        if not self.emulator_name:
            wx.MessageBox("You need to set up an emulator first.", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        with wx.FileDialog(self, "Select game executable", defaultDir=self.game_lib,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dlg:
            if file_dlg.ShowModal() == wx.ID_CANCEL:
                return
            path = file_dlg.GetPath()

        with wx.TextEntryDialog(self, 'Name of the game?', 'Add a game') as name_dlg:
            if name_dlg.ShowModal() == wx.ID_OK:
                game_name = name_dlg.GetValue()
                if any(details['Game'] == game_name and details['Application'] == self.emulator_name 
                       for details in self.games_dict.values()):
                    wx.MessageBox(f"The game '{game_name}' is already setup for this emulator.", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
                    return

                new_id = str(uuid.uuid4())
                self.games_dict[new_id] = {
                    'Game': game_name,
                    'Application': self.emulator_name,
                    'Options': f' "{path}" {self.default_option}',
                    'Notes': ''
                }
                self.current_game_id = new_id
                self.filter_the_games(True)

    def on_edit_game_name(self, event):
        if not self.current_game_id or self.current_game_id not in self.games_dict:
            wx.MessageBox("Nothing to edit", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        current_details = self.games_dict[self.current_game_id]
        with wx.TextEntryDialog(self, 'Change the name?', 'Edit a game', value=current_details['Game']) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                new_name = dlg.GetValue()
                self.games_dict[self.current_game_id]['Game'] = new_name
                self.filter_the_games(True)

    def on_delete_game(self, event):
        if not self.current_game_id or self.current_game_id not in self.games_dict:
            wx.MessageBox("Nothing to delete", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        msg = f"Do you really want to delete '{self.games_dict[self.current_game_id]['Game']}'?"
        with wx.MessageDialog(self, msg, 'Are you sure?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) as dlg:
            if dlg.ShowModal() == wx.ID_YES:
                del self.games_dict[self.current_game_id]
                self.current_game_id = ''
                self.filter_the_games(True)

    def on_add_emu(self, event):
        with wx.TextEntryDialog(self, 'Name of the Emulator?', 'Add an emulator') as name_dlg:
            if name_dlg.ShowModal() != wx.ID_OK:
                return
            emu_name = name_dlg.GetValue()
            if emu_name in self.emu_dict:
                wx.MessageBox(f"The emulator '{emu_name}' is already setup", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
                return

        with wx.FileDialog(self, "Select the emulator's executable", defaultDir=self.game_lib,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as exe_dlg:
            if exe_dlg.ShowModal() != wx.ID_OK:
                return
            exe_path = exe_dlg.GetPath()
            working_dir = exe_dlg.GetDirectory()

        with wx.DirDialog(self, "Select the emulator's default games directory", defaultPath=self.game_lib) as dir_dlg:
            path2 = dir_dlg.GetPath() if dir_dlg.ShowModal() == wx.ID_OK else ''

        with wx.TextEntryDialog(self, 'Any default options to add to new games?', 'Default Options') as opt_dlg:
            default_local = opt_dlg.GetValue() if opt_dlg.ShowModal() == wx.ID_OK else ""

        self.emu_dict[emu_name] = {
            'Location': f'"{exe_path}"',
            'Library_default': path2,
            'Default_option': default_local,
            'Working_Directory': working_dir
        }
        self.emulator_list = sorted(list(self.emu_dict.keys()))
        self.choice_of_emu.SetItems(self.emulator_list)
        self.choice_of_emu.SetStringSelection(emu_name)
        self.emulator_name = emu_name
        self.filter_the_games(True)

    def on_edit_emu(self, event):
        if not self.emulator_name:
            return

        with wx.TextEntryDialog(self, 'Change the name of the emulator?', 'Edit emulator', value=self.emulator_name) as name_dlg:
            if name_dlg.ShowModal() != wx.ID_OK:
                return
            new_emu_name = name_dlg.GetValue()

        current_exe = self.emu_dict[self.emulator_name]["Location"].strip('"')
        with wx.FileDialog(self, "Select the emulator's executable", defaultFile=current_exe) as exe_dlg:
            if exe_dlg.ShowModal() == wx.ID_OK:
                exe_path = exe_dlg.GetPath()
                working_dir = exe_dlg.GetDirectory()
            else:
                exe_path = current_exe
                working_dir = self.emu_dict[self.emulator_name]['Working_Directory']

        current_lib = self.emu_dict[self.emulator_name]['Library_default']
        with wx.DirDialog(self, "Select the emulator's default games directory", defaultPath=current_lib) as dir_dlg:
            lib_path = dir_dlg.GetPath() if dir_dlg.ShowModal() == wx.ID_OK else current_lib

        current_opt = self.emu_dict[self.emulator_name]['Default_option']
        with wx.TextEntryDialog(self, 'Default options?', 'Edit Options', value=current_opt) as opt_dlg:
            opt_val = opt_dlg.GetValue() if opt_dlg.ShowModal() == wx.ID_OK else current_opt

        # Update all games associated with this emulator if name changed
        if new_emu_name != self.emulator_name:
            for game_id in self.games_dict:
                if self.games_dict[game_id]['Application'] == self.emulator_name:
                    self.games_dict[game_id]['Application'] = new_emu_name
            self.emu_dict[new_emu_name] = self.emu_dict.pop(self.emulator_name)

        self.emu_dict[new_emu_name].update({
            'Location': f'"{exe_path}"',
            'Library_default': lib_path,
            'Default_option': opt_val,
            'Working_Directory': working_dir
        })
        
        self.emulator_list = sorted(list(self.emu_dict.keys()))
        self.choice_of_emu.SetItems(self.emulator_list)
        self.choice_of_emu.SetStringSelection(new_emu_name)
        self.emulator_name = new_emu_name
        self.filter_the_games(True)

    def on_delete_emu(self, event):
        if not self.emulator_name:
            return

        msg = f"Delete '{self.emulator_name}' and ALL its games?"
        with wx.MessageDialog(self, msg, 'Are you sure?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_STOP) as dlg:
            if dlg.ShowModal() == wx.ID_YES:
                # Remove games
                games_to_del = [gid for gid, details in self.games_dict.items() if details['Application'] == self.emulator_name]
                for gid in games_to_del:
                    del self.games_dict[gid]
                
                del self.emu_dict[self.emulator_name]
                self.emulator_list = sorted(list(self.emu_dict.keys()))
                self.choice_of_emu.SetItems(self.emulator_list)
                if self.emulator_list:
                    self.emulator_name = self.emulator_list[0]
                    self.choice_of_emu.SetStringSelection(self.emulator_name)
                else:
                    self.emulator_name = ""
                    self.choice_of_emu.SetValue("")
                self.filter_the_games(True)

    def on_file_open(self, event):
        """Add a file path to the current game's options"""
        if not self.current_game_id or self.current_game_id not in self.games_dict:
            wx.MessageBox("No game selected.", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        with wx.FileDialog(self, "Select file to add to options", defaultDir=self.game_lib,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                current_options = self.games_dict[self.current_game_id]["Options"]
                self.games_dict[self.current_game_id]["Options"] = f'{current_options} "{path}"'
                self.on_list_select(None)

    def on_run_game(self, event):
        emu_path = self.emu_location.GetValue()
        if not emu_path:
            wx.MessageBox("No emulator executable selected.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Ensure emu_path is quoted if it contains spaces and is not already quoted
        # We strip quotes first to avoid double quoting if it was somehow already quoted
        emu_path = emu_path.strip('"')
        if ' ' in emu_path:
            emu_path = f'"{emu_path}"'

        if len(self.filtered_game_list) > 0:
            select_index = self.my_list.GetSelection()
            if select_index == wx.NOT_FOUND:
                wx.MessageBox("Please select a game to play.", "Info", wx.OK | wx.ICON_INFORMATION)
                return

            game_name = self.filtered_game_list[select_index]
            self.current_game_id = self.game_index_dict[game_name]
            options = self.games_dict[self.current_game_id]["Options"]
            
            # Construct the command correctly for Windows.
            # We must not wrap the entire command in an extra set of quotes as it causes
            # cmd.exe to fail parsing quoted paths correctly.
            cmd = f'{emu_path} {options}'
            
            try:
                subprocess.Popen(cmd, cwd=self.working_directory, shell=True)
            except Exception as e:
                wx.MessageBox(f"Failed to start game: {e}", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("The emulator hasn't got any games set up",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def on_double_click(self, event):
        self.on_run_game(None)

    def on_list_select(self, event):
        """Update the UI based on the selected game."""
        select_index = self.my_list.GetSelection()
        if select_index == wx.NOT_FOUND:
            return

        game_name = self.filtered_game_list[select_index]
        self.current_game_id = self.game_index_dict[game_name]

        # update items related to what has been selected
        self.run_options.SetValue(self.games_dict[self.current_game_id]['Options'])
        self.game_notes.SetValue(self.games_dict[self.current_game_id]['Notes'])
        
        # Display correctly quoted string for CMD
        emu_path = self.emu_executable.strip('"')
        if ' ' in emu_path:
            emu_path = f'"{emu_path}"'
        self.cmd_string.SetValue(f"{emu_path} {self.games_dict[self.current_game_id]['Options']}")

    def on_emulator_change(self, event):
        self.emulator_name = self.choice_of_emu.GetStringSelection()
        self.filter_the_games(False)

    def filter_the_games(self, save_data):
        """Filter the games list based on the selected emulator."""
        if self.emulator_list:
            if save_data:
                self.data_manager.save_data()

            if self.emulator_name not in self.emu_dict:
                self.emulator_name = self.emulator_list[0] if self.emulator_list else ""

            if self.emulator_name:
                emu_data = self.emu_dict[self.emulator_name]
                # Store raw path in the UI control for display and execution
                raw_emu_path = emu_data['Location'].strip('"')
                self.emu_location.SetValue(raw_emu_path)
                self.emu_executable = raw_emu_path
                self.game_location.SetValue(emu_data['Library_default'])
                self.game_lib = emu_data['Library_default']
                self.default_opt_ctrl.SetValue(emu_data['Default_option'])
                self.default_option = emu_data['Default_option']
                self.cwd.SetValue(emu_data['Working_Directory'])
                self.working_directory = emu_data['Working_Directory']
        else:
            self.emu_location.SetValue('')
            self.game_location.SetValue('')
            self.cmd_string.SetValue('')

        self.filtered_game_list = []
        self.game_index_dict = {}
        for game_id, details in self.games_dict.items():
            if details['Application'] == self.emulator_name:
                game_name = details['Game']
                self.filtered_game_list.append(game_name)
                self.game_index_dict[game_name] = game_id
        self.filtered_game_list.sort()

        self.my_list.Set(self.filtered_game_list)

        if self.filtered_game_list:
            # Try to maintain selection or pick first
            current_game_name = self.games_dict.get(self.current_game_id, {}).get('Game', '')
            if current_game_name in self.filtered_game_list:
                current_selection = self.filtered_game_list.index(current_game_name)
            else:
                current_selection = 0
            
            self.my_list.SetSelection(current_selection)
            self.on_list_select(None)
        else:
            self.run_options.SetValue('')
            self.game_notes.SetValue('')
            self.cmd_string.SetValue('')

    def on_update_game_details(self, event):
        """Update current game options and notes."""
        if self.filtered_game_list:
            if self.current_game_id not in self.games_dict:
                return
            
            self.games_dict[self.current_game_id]["Options"] = self.run_options.GetValue()
            self.games_dict[self.current_game_id]["Notes"] = self.game_notes.GetValue()
            
            # Display correctly quoted string for CMD
            emu_path = self.emu_executable.strip('"')
            if ' ' in emu_path:
                emu_path = f'"{emu_path}"'
            self.cmd_string.SetValue(f"{emu_path} {self.games_dict[self.current_game_id]['Options']}")
            self.data_manager.save_data()
            
            game_name = self.games_dict[self.current_game_id]["Game"]
            wx.MessageBox(f'Details updated for {game_name}', 'Done', wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("There are no games set up yet..", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)

def main():
    app = wx.App()
    MyFrame()
    app.MainLoop()


if __name__ == '__main__':
    main()
