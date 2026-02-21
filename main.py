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
        self.datastorelocation = os.path.join(os.getenv("USERPROFILE", ""), "AppData", "Local", "RetroRoaming")
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
        self.emulator = sorted(list(self.emu_dict.keys()))
        if self.emulator:
            self.emulator_name = self.emulator[0]
        else:
            self.emulator_name = ''

        # Sets up variables used in the program
        self.dosbox_loc = ''
        self.game_lib = ''
        self.current_game = ''
        self.run_syntax = ''
        self.default_option = ''
        self.working_directory = ''
        self.filtered_game_list = []
        self.game_index_dict = {}

        # UI Elements
        self.my_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.runoptions = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.cwd = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.default = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.gamenotes = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.emu_location = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.game_location = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.cmdstring = wx.TextCtrl(panel, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.cmdstring.SetForegroundColour((0, 255, 0))
        self.cmdstring.SetBackgroundColour((0, 0, 0))

        self.choice_of_emu = wx.ComboBox(panel, choices=self.emulator, style=wx.CB_READONLY)

        # Buttons
        my_btn = wx.Button(panel, label='Play Game', size=(100, 30))
        my_btn_edit = wx.Button(panel, label='Update', size=(100, 30))
        my_btn_exit = wx.Button(panel, label='Exit', size=(100, 30))

        # Bindings
        my_btn.Bind(wx.EVT_BUTTON, self.run_game)
        my_btn_edit.Bind(wx.EVT_BUTTON, self.onedit)
        my_btn_exit.Bind(wx.EVT_BUTTON, self.on_exit)
        self.my_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_doubleclk)
        self.my_list.Bind(wx.EVT_LISTBOX, self.on_clk)
        self.choice_of_emu.Bind(wx.EVT_COMBOBOX, self.filterchange)

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
        right_sizer.Add(self.runoptions, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Default option added to new games:"), 0, wx.ALL, 5)
        right_sizer.Add(self.default, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="Notes on how to play:"), 0, wx.ALL, 5)
        right_sizer.Add(self.gamenotes, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticText(panel, label="This will run at command prompt:"), 0, wx.ALL, 5)
        right_sizer.Add(self.cmdstring, 0, wx.EXPAND | wx.ALL, 5)

        button_sizer.Add(my_btn, 0, wx.ALL, 5)
        button_sizer.Add(my_btn_edit, 0, wx.ALL, 5)
        button_sizer.Add(my_btn_exit, 0, wx.ALL, 5)
        right_sizer.Add(button_sizer, 0, wx.CENTER)

        panel.SetSizer(main_sizer)

        # Initialize UI state
        if self.emulator_name:
            self.choice_of_emu.SetValue(self.emulator_name)
        self.filterthegames(False)

        self.make_menu_bar()
        self.Show()

    def on_exit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def make_menu_bar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        file_menu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        # helloItem = file_menu.Append(-1, "&Hello...\tCtrl-H",
        #                            "Help string shown in status bar for this menu item")
        fileopenitem = file_menu.Append(-1, "&Add file location to Options\tCtrl-F",
                                        "If you want to reference a file location in options this will add it")
        # emuLocationItem = file_menu.Append(-1, "Emulator Location")
        file_menu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exititem = file_menu.Append(wx.ID_EXIT)

        # Add the edit game menu
        editmenu = wx.Menu()
        additem = editmenu.Append(-1, "&Add Game\tCtrl-A",
                                  "This sets up a new game record in the library")
        edititem = editmenu.Append(-1, "&Edit Game\tCtrl-E",
                                   "Allows you to changes details on the game in the library")
        deleteitem = editmenu.Append(-1, "&Delete Game\tCtrl-D",
                                     "Remove the game from you library")

        # Add the emulator game menu
        editemumenu = wx.Menu()
        addemuitem = editemumenu.Append(-1, "&Add Emulator",
                                        "Add executable to start the emulator use options to pass parameters")
        editemuitem = editemumenu.Append(-1, "&Edit Emulator",
                                         "Edit details of the emulator set up")
        delemuitem = editemumenu.Append(-1, "&Delete Emulator",
                                        "Remove the emulator - this will also remove the library of games")

        # Now a help menu for the about item
        helpmenu = wx.Menu()
        aboutitem = helpmenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menubar = wx.MenuBar()
        menubar.Append(file_menu, "&File")
        menubar.Append(editmenu, "&Edit Game")
        menubar.Append(editemumenu, "&Edit Emulator")
        menubar.Append(helpmenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menubar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        # self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.on_exit, exititem)
        self.Bind(wx.EVT_MENU, self.onabout, aboutitem)
        self.Bind(wx.EVT_MENU, self.onfileopen, fileopenitem)
        # self.Bind(wx.EVT_MENU, self.emulatorDialog, emuLocationItem)
        self.Bind(wx.EVT_MENU, self.addgame, additem)
        self.Bind(wx.EVT_MENU, self.editgame, edititem)
        self.Bind(wx.EVT_MENU, self.deletegame, deleteitem)
        self.Bind(wx.EVT_MENU, self.addemu, addemuitem)
        self.Bind(wx.EVT_MENU, self.editemu, editemuitem)
        self.Bind(wx.EVT_MENU, self.deleteemu, delemuitem)

    def onexit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def onabout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("Retro Roaming, allowing you to run and organise your games.\n\n"
                      "Written by Adam Thirlwell (thirlwella@gmail.com)\n"
                      "Updated Feb 2026 by Junie",
                      "About Retro Roaming",
                      wx.OK | wx.ICON_INFORMATION | wx.CENTER)

    def addgame(self, event):
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
                gamename = name_dlg.GetValue()
                if any(details['Game'] == gamename and details['Application'] == self.emulator_name 
                       for details in self.games_dict.values()):
                    wx.MessageBox(f"The game '{gamename}' is already setup for this emulator.", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
                    return

                new_id = str(uuid.uuid4())
                self.games_dict[new_id] = {
                    'Game': gamename,
                    'Application': self.emulator_name,
                    'Options': f' "{path}" {self.default_option}',
                    'Notes': ''
                }
                self.current_game = new_id
                self.filterthegames(True)

    def editgame(self, event):
        if not self.current_game or self.current_game not in self.games_dict:
            wx.MessageBox("Nothing to edit", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        current_details = self.games_dict[self.current_game]
        with wx.TextEntryDialog(self, 'Change the name?', 'Edit a game', value=current_details['Game']) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                new_name = dlg.GetValue()
                self.games_dict[self.current_game]['Game'] = new_name
                self.filterthegames(True)

    def deletegame(self, event):
        if not self.current_game or self.current_game not in self.games_dict:
            wx.MessageBox("Nothing to delete", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        msg = f"Do you really want to delete '{self.games_dict[self.current_game]['Game']}'?"
        with wx.MessageDialog(self, msg, 'Are you sure?', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) as dlg:
            if dlg.ShowModal() == wx.ID_YES:
                del self.games_dict[self.current_game]
                self.current_game = ''
                self.filterthegames(True)

    def addemu(self, event):
        with wx.TextEntryDialog(self, 'Name of the Emulator?', 'Add an emulator') as name_dlg:
            if name_dlg.ShowModal() != wx.ID_OK:
                return
            emuname = name_dlg.GetValue()
            if emuname in self.emu_dict:
                wx.MessageBox(f"The emulator '{emuname}' is already setup", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
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

        self.emu_dict[emuname] = {
            'Location': f'"{exe_path}"',
            'Library_default': path2,
            'Default_option': default_local,
            'Working_Directory': working_dir
        }
        self.emulator = sorted(list(self.emu_dict.keys()))
        self.choice_of_emu.SetItems(self.emulator)
        self.choice_of_emu.SetStringSelection(emuname)
        self.emulator_name = emuname
        self.filterthegames(True)

    def editemu(self, event):
        if not self.emulator_name:
            return

        with wx.TextEntryDialog(self, 'Change the name of the emulator?', 'Edit emulator', value=self.emulator_name) as name_dlg:
            if name_dlg.ShowModal() != wx.ID_OK:
                return
            new_emuname = name_dlg.GetValue()

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
        if new_emuname != self.emulator_name:
            for game_id in self.games_dict:
                if self.games_dict[game_id]['Application'] == self.emulator_name:
                    self.games_dict[game_id]['Application'] = new_emuname
            self.emu_dict[new_emuname] = self.emu_dict.pop(self.emulator_name)

        self.emu_dict[new_emuname].update({
            'Location': f'"{exe_path}"',
            'Library_default': lib_path,
            'Default_option': opt_val,
            'Working_Directory': working_dir
        })
        
        self.emulator = sorted(list(self.emu_dict.keys()))
        self.choice_of_emu.SetItems(self.emulator)
        self.choice_of_emu.SetStringSelection(new_emuname)
        self.emulator_name = new_emuname
        self.filterthegames(True)

    def deleteemu(self, event):
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
                self.emulator = sorted(list(self.emu_dict.keys()))
                self.choice_of_emu.SetItems(self.emulator)
                if self.emulator:
                    self.emulator_name = self.emulator[0]
                    self.choice_of_emu.SetStringSelection(self.emulator_name)
                else:
                    self.emulator_name = ""
                    self.choice_of_emu.SetValue("")
                self.filterthegames(True)

    def onfileopen(self, event):
        """Add a file path to the current game's options"""
        if not self.current_game or self.current_game not in self.games_dict:
            wx.MessageBox("No game selected.", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)
            return

        with wx.FileDialog(self, "Select file to add to options", defaultDir=self.game_lib,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                current_options = self.games_dict[self.current_game]["Options"]
                self.games_dict[self.current_game]["Options"] = f'{current_options} "{path}"'
                self.on_clk(None)

    def run_game(self, event):
        emu_path = self.emu_location.GetValue()
        if not emu_path:
            wx.MessageBox("No emulator executable selected.", "Error", wx.OK | wx.ICON_ERROR)
            return

        if len(self.filtered_game_list) > 0:
            select_index = self.my_list.GetSelection()
            if select_index == wx.NOT_FOUND:
                wx.MessageBox("Please select a game to play.", "Info", wx.OK | wx.ICON_INFORMATION)
                return

            self.listed_game = self.choice_of_games[select_index]
            self.current_game = self.game_index_dict[self.listed_game]
            options = self.games_dict[self.current_game]["Options"]
            
            # Simple command construction. 
            doscmd = f"\"{emu_path}\" {options}"
            
            try:
                subprocess.Popen(doscmd, cwd=self.working_directory, shell=True)
            except Exception as e:
                wx.MessageBox(f"Failed to start game: {e}", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox(f"The emulator hasn't got any games set up",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def on_doubleclk(self, event):
        self.run_game(None)

    # Needs to be called if you want to change focus to a different game to update the screen
    def on_clk(self, event):
        select_index = self.my_list.GetSelection()
        if select_index == wx.NOT_FOUND:
            return

        self.listed_game = self.choice_of_games[select_index]
        self.current_game = self.game_index_dict[self.listed_game]

        # update items related to what has been selected
        self.runoptions.SetValue(self.games_dict[self.current_game]['Options'])
        self.gamenotes.SetValue(self.games_dict[self.current_game]['Notes'])
        self.cmdstring.SetValue('\"' + self.dosbox_loc + '\" ' + self.games_dict[self.current_game]['Options'])

    def filterchange(self, event):
        self.emulator_name = self.choice_of_emu.GetStringSelection()
        self.filterthegames(False)

    # This def needs to be called when the emulator or details about it change
    # It updates the global variables used
    def filterthegames(self, save_or_not):
        if self.emulator:
            if save_or_not:
                self.data_manager.save_data()

            if self.emulator_name not in self.emu_dict:
                if self.emulator:
                    self.emulator_name = self.emulator[0]
                else:
                    self.emulator_name = ""

            if self.emulator_name:
                emu_data = self.emu_dict[self.emulator_name]
                self.emu_location.SetValue(emu_data['Location'])
                self.dosbox_loc = emu_data['Location']
                self.game_location.SetValue(emu_data['Library_default'])
                self.game_lib = emu_data['Library_default']
                self.default.SetValue(emu_data['Default_option'])
                self.default_option = emu_data['Default_option']
                self.cwd.SetValue(emu_data['Working_Directory'])
                self.working_directory = emu_data['Working_Directory']
        else:
            self.emu_location.SetValue('')
            self.game_location.SetValue('')
            self.cmdstring.SetValue('')

        self.filtered_game_list = []
        self.game_index_dict = {}
        for x, details in self.games_dict.items():
            if details['Application'] == self.emulator_name:
                game_name = details['Game']
                self.filtered_game_list.append(game_name)
                self.game_index_dict[game_name] = x
        self.filtered_game_list.sort()

        self.choice_of_games = self.filtered_game_list
        self.my_list.Set(self.choice_of_games)

        if self.filtered_game_list:
            # Try to maintain selection or pick first
            try:
                # Find by name if possible
                current_game_name = self.games_dict.get(self.current_game, {}).get('Game', '')
                if current_game_name in self.filtered_game_list:
                    current_selection = self.filtered_game_list.index(current_game_name)
                else:
                    current_selection = 0
            except Exception:
                current_selection = 0
            
            self.my_list.SetSelection(current_selection)
            self.on_clk(None)
        else:
            self.runoptions.SetValue('')
            self.gamenotes.SetValue('')
            self.cmdstring.SetValue('')

    # ----------------------------------------------------------------------

    def onedit(self, event):
        if len(self.filtered_game_list) > 0:
            if self.current_game not in self.games_dict:
                return
            
            self.games_dict[self.current_game]["Options"] = self.runoptions.GetValue()
            self.games_dict[self.current_game]["Notes"] = self.gamenotes.GetValue()
            
            self.cmdstring.SetValue(self.dosbox_loc + ' ' + self.games_dict[self.current_game]['Options'])
            self.data_manager.save_data()
            
            wx.MessageBox(f'Details updated for {self.listed_game}', 'Done', wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("There are no games set up yet..", "Warning", wx.OK | wx.ICON_STOP | wx.CENTER)

def main():
    app = wx.App()
    MyFrame()
    app.MainLoop()


if __name__ == '__main__':
    main()
