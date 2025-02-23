#
# Retro Roaming written by Adam Thirlwell June 2021
# Update Nov 2023 - add status bar details 1.01
#
# Done: Add ability to rename a game
# Done: Add ability to rename an emulator
# Done Jan 2025: change order when you add a game, browse to file first then name
# Done Jan 2025: ability to start a game by double click
# Done: allow a game of the same name with a different emulator
# Done: Add a default option for an emulator, e.g. screen size for Fuse
# To do: add change working directory option.
# Done: Update 'onedit' to show the game name not the UID
#
# import sys
import wx
import os
# import wx.dataview as dv
import subprocess
import json
import uuid


# File being loaded at the start need to add saving and creating new file if one is not there


# emu_dict = {'DosBox': {'Location': '"E:\\Program Files (x86)\\DOSBox-0.74-3\\DOSBox.exe"',
#                                       'Library_default': 'E:\\Dos\\DosGames\\'},
#          'ZXSpectrum': {'Location': '"E:\\Program Files (x86)\\Fuse\\Fuse.exe"',
#                                     'Library_default': 'E:\\Dos\\DosGames\\Emu\\Speccy\\Games'},
#        'AmstradCPC':{'Location': '"E:\\Amstrad\\CpcLoad\\cpcload.exe"',
#                                   'Library_default': 'E:\\Amstrad\\' }
#      }


class MyFrame(wx.Frame):

    def __init__(self):
        super().__init__(parent=None, title='Retro Roaming', size=(1200, 800))
        panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar(1)
        # Frame uses 3 sizers
        my_sizer = wx.BoxSizer(wx.HORIZONTAL)
        my_sizer2 = wx.BoxSizer(wx.VERTICAL)
        my_sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        # Set up button details will be added to my_sizer3
        my_btn = wx.Button(panel, label='Play Game', size=(100, 30))
        my_btn.Bind(wx.EVT_BUTTON, self.run_game)
        my_btn_edit = wx.Button(panel, label='Update', size=(100, 30))
        my_btn_edit.Bind(wx.EVT_BUTTON, self.onedit)
        my_btn_exit = wx.Button(panel, label='Exit', size=(100, 30))
        my_btn_exit.Bind(wx.EVT_BUTTON, self.on_exit)

        # Set up the variables to be used
        # with open('emulist.json', 'w') as fp:
        #   json.dump(emu_dict, fp,  indent=4)

        # Need to load the data saved to your profile, if it is already there
        # If the directory does not exist then create it
        self.datastorelocation = os.getenv("USERPROFILE") + '\\AppData\\Local\\RetroRoaming\\'
        if not os.path.exists(self.datastorelocation):
            os.makedirs(self.datastorelocation)
        # These are the 2 data files the program needs. Details of Emulators and Games
        self.emu_file = self.datastorelocation + 'emu_data.json'
        self.game_file = self.datastorelocation + 'games_data.json'
        # Defines this as blank dictionaries for when the files don't exist
        self.emu_dict = {}
        self.games_dict = {}
        # Checks to see if the json files are there and loads them if they are
        if not os.path.isfile(self.emu_file):
            wx.MessageBox(f"No data files found in your profile, new ones will be created in {self.datastorelocation}",
                          "No files found",
                          wx.OK | wx.CENTER)
        else:
            self.emu_dict = json.load(open(self.emu_file, 'r'))
            if not os.path.isfile(self.game_file):
                wx.MessageBox(
                    f"Game file is missing for some reason.. {self.datastorelocation}",
                    "No Games file found",
                    wx.OK | wx.CENTER)
            else:
                self.games_dict = json.load(open(self.game_file, 'r'))
        # Gets a list of the emulators and picks the first one
        self.emulator = list(self.emu_dict.keys())
        if len(self.emulator) > 0:
            self.emulator.sort()
            self.emulator_name = next(iter(self.emu_dict.keys()))
        else:
            self.emulator_name = ''

        # Sets up variables used in the program
        self.dosbox_loc = ''
        self.game_lib = ''
        self.current_game = ''
        self.run_syntax = ''
        self.default_option = ''
        self.working_directory = ''
        # Needs to move to json file, how will it work if this is the first record, need ability to add a game first
        # self.games_dict = {'Doom': {'Application': 'DosBox',
        #                'Options':' -conf "E:\\Dos\\dosboxconf\\doom2-0.74-3.conf" "E:\Dos\DosGames\DOOM2\DOOM2.EXE"'},
        #                   'Lemmings': {'Application': 'DosBox',
        #                                'Options': '"E:\\Dos\\DosGames\\Lemmings\\LEMVGA.COM"'},
        #                   'sdfsfsfsdfs': {'Application': 'DosBox', 'Options': 'stuff here sdsds'},
        #                   'Manic Miner': {'Application': 'ZXSpectrum',
        #                                   'Options': '"E:\Dos\DosGames\Emu\Speccy\Games\Manic.z80" -g 3x'},
        #                   'Jetpac': {'Application': 'ZXSpectrum',
        #                              'Options': '"E:\Dos\DosGames\Emu\Speccy\Games\Jetpac.z80" -g 3x'},
        #                   'Games Library': {'Application': 'AmstradCPC', 'Options': '--explorer --max'}
        #                   }
        # select just the games for the emulator selected
        self.filtered_game_list = []

        self.choice_of_games = self.filtered_game_list
        self.my_list = wx.ListBox(panel, 1, choices=list(self.choice_of_games), style=wx.LB_SINGLE)
        # self.param_1_type = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.runoptions = wx.TextCtrl(panel, 1, style=wx.TE_MULTILINE)
        self.cwd = wx.TextCtrl(panel, 1, self.working_directory, style=wx.TE_READONLY)
        self.default = wx.TextCtrl(panel, 1, style=wx.TE_READONLY)
        self.gamenotes = wx.TextCtrl(panel, 1, style=wx.TE_MULTILINE)
        self.emu_location = wx.TextCtrl(panel, 1, self.dosbox_loc, style=wx.TE_READONLY)
        self.game_location = wx.TextCtrl(panel, 1, self.game_lib, style=wx.TE_READONLY)
        self.cmdstring = wx.TextCtrl(panel, 1, self.run_syntax, style=wx.TE_READONLY | wx.TE_MULTILINE)
        # change colour of text
        self.cmdstring.SetForegroundColour((0, 255, 0))
        self.cmdstring.SetBackgroundColour((0, 0, 0))
        self.choice_of_emu = wx.ComboBox(panel,
                                         size=wx.DefaultSize,
                                         choices=self.emulator,
                                         style=wx.TE_READONLY)
        self.my_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_doubleclk)
        self.my_list.Bind(wx.EVT_LISTBOX, self.on_clk)
        self.choice_of_emu.Bind(wx.EVT_TEXT, self.filterchange)

        # Get the screen to update with the first selected of the first emulator and game when opened
        self.choice_of_emu.SetValue(self.emulator_name)
        self.filterthegames(False)
        #
        # self.choice_of_emu.SetSelection(1)
        # self.filterthegames(1)
        # self.my_list.SetSelection(1)
        # self.on_clk(self.my_list.SetSelection(1))

        # my_sizer.AddSpacer(20)
        # panel.SetSizer(my_sizer)

        my_sizer.Add(self.my_list,
                     1,  # make vertically stretchable (ratio)
                     wx.EXPAND |  # make horizontally stretchable
                     wx.ALL,  # and make border all around
                     5)  # set border width

        my_sizer.Add(my_sizer2, 1, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(wx.StaticText(panel, -1, "Emulator Selected : "), 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(self.choice_of_emu, 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(wx.StaticText(panel, -1, "Location of emulator executable: "), 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(self.emu_location, 0, wx.ALL | wx.EXPAND, 5)
        # my_sizer2.Add(self.param_1_type, 0, wx.ALL | wx.EXPAND, 5)
        # added Feb 2025
        my_sizer2.Add(wx.StaticText(panel, -1, "Working Directory : "), 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(self.cwd, 0, wx.ALL | wx.EXPAND, 5)
        #
        my_sizer2.Add(wx.StaticText(panel, -1, "Default Game Library Location : "), 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(self.game_location, 0, wx.ALL | wx.EXPAND, 5)
        #
        my_sizer2.Add(wx.StaticText(panel, -1, "Parameters passed to executable: "), 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(self.runoptions, 0, wx.ALL | wx.EXPAND, 5)
        # added Feb 2025
        my_sizer2.Add(wx.StaticText(panel, -1, "Default option added to new games: "),
                      0, wx.ALL | wx.EXPAND, 5)
        #
        my_sizer2.Add(self.default, 0, wx.LEFT | wx.EXPAND, 5)
        my_sizer2.Add(wx.StaticText(panel, -1, "Notes on how to play: "), 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(self.gamenotes, 2, wx.ALL | wx.EXPAND, 5)

        # self.text_ctrl.SetValue('Blimey')
        # my_sizer2.Add(wx.StaticText(panel, -1, "Games:"), 0, wx.ALL | wx.CENTER, 5)

        my_sizer2.Add(wx.StaticText(panel, -1, "This will run at command prompt : "),
                      0,  # horizontally stretchable (ratio)
                      wx.ALL |  # Border all around
                      wx.EXPAND,  # vertically stretchable (can add more if wanted using "|")
                      5)  # size of border
        my_sizer2.Add(self.cmdstring, 0, wx.ALL | wx.EXPAND, 5)
        my_sizer2.Add(my_sizer3, 0, wx.ALL | wx.CENTER, 5)
        my_sizer3.Add(my_btn, 0, wx.ALL | wx.CENTER, 5)
        my_sizer3.Add(my_btn_edit, 0, wx.ALL | wx.CENTER, 5)
        my_sizer3.Add(my_btn_exit, 0, wx.ALL | wx.CENTER, 5)
        panel.SetSizer(my_sizer)

        # create a menu bar
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
        wx.MessageBox("Retro Roaming, allowing you to run and organise your games."
                      "\r\rAdam Thirlwell (thirlwella@gmail.com)\r\r version 1.1",
                      "About Retro Roaming",
                      wx.OK | wx.ICON_INFORMATION | wx.CENTER)

    def addgame(self, event):
        # Adds a record to the list using current view
        #  'sdfsfsfsdfs': {'Application': 'DosBox', 'Options': 'stuff here sdsds'},
        #

        if len(self.emulator) > 0:
            # select the game file.
            dlg = wx.FileDialog(
                self, message="Select game executable",
                # defaultPath= os.getenv("USERPROFILE"),
                defaultDir=self.game_lib,
                style=wx.DD_DEFAULT_STYLE)

            # Show the dialog and retrieve the user response.
            if dlg.ShowModal() == wx.ID_OK:
                # load directory
                path = dlg.GetPath()

            else:
                path = ''

                # Destroy the dialog.
            dlg.Destroy()
            # Update the screen again this time saving the changes
            dlg = wx.TextEntryDialog(
                self, 'Name of the games is?',
                'Add a game', '?')
            # dlg.SetValue("Python is the best!")
            if dlg.ShowModal() == wx.ID_OK:
                # self.log.WriteText('You entered: %s\n' % dlg.GetValue())

                gamename = dlg.GetValue()
                if gamename not in self.filtered_game_list:

                    new_index_for_game = str(uuid.uuid4())
                    # check that UID is not already in user (add later)

                    self.games_dict[new_index_for_game] = {'Game': gamename,
                                                           'Application': self.emulator_name,
                                                           'Options': ' "' + path + '" ' + self.default_option,
                                                           'Notes': ''}


                    #self.games_dict[gamename] = {'Application': self.emulator_name, 'Options': '', 'Notes': ''}


                    # Update the options

                    #options_before = self.games_dict[self.current_game]["Options"]
                    #self.games_dict[self.current_game]["Options"] = options_before + ' "' + path + '" ' + \
                    #                                                self.default_option
                    # update the screen
                    self.current_game = gamename
                    self.filterthegames(False)
                    # Call the function to add the file (screen needs to update first to select the new game)
                    # self.onfileopen(self)
                    # Update the screen again this time saving the changes
                    self.filterthegames(True)
                else:
                    wx.MessageBox(f"The game {gamename} is already setup",
                                  "Warning",
                                  wx.OK | wx.ICON_STOP | wx.CENTER)
            dlg.Destroy()
        else:
            wx.MessageBox(f"You need to set up an emulator first..",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def editgame(self, event):
        # Edits a record
        #  'sdfsfsfsdfs': {'Application': 'DosBox', 'Options': 'stuff here sdsds'},
        #
        select_index = self.my_list.GetSelection()
        self.listed_game = self.choice_of_games[select_index]
        self.current_game = self.game_index_dict[self.listed_game]

        if self.current_game in self.games_dict.keys():



            #self.current_game = self.choice_of_games[select_index]


            selectoption = self.games_dict[self.current_game]["Options"]
            dlg = wx.TextEntryDialog(
                self, 'Change the name?',
                'Edit a game', '?')
            dlg.SetValue(self.listed_game)
            if dlg.ShowModal() == wx.ID_OK:
                # self.log.WriteText('You entered: %s\n' % dlg.GetValue())
                gamename_new = dlg.GetValue()

                del self.games_dict[self.current_game]
                new_index_for_game = str(uuid.uuid4())
                # check that UID is not already in user (add later)

                self.games_dict[new_index_for_game] = {'Game' : gamename_new,
                                                 'Application': self.emulator_name,
                                                 'Options': selectoption,
                                                 'Notes': self.gamenotes.Value}
                self.current_game = gamename_new
                self.filterthegames(True)

            dlg.Destroy()
        else:
            wx.MessageBox(f"Nothing to edit",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def deletegame(self, event):

        if self.current_game in self.games_dict.keys():

            dlg = wx.MessageDialog(self, f'Do you really want to delete {self.listed_game}',
                                   'Are you sure?',
                                   # wx.OK | wx.ICON_INFORMATION
                                   wx.OK | wx.CANCEL | wx.ICON_STOP
                                   )
            if dlg.ShowModal() == wx.ID_OK:
                # self.log.WriteText('You entered: %s\n' % dlg.GetValue())

                del self.games_dict[self.current_game]
                self.filterthegames(True)
            dlg.Destroy()
        else:
            wx.MessageBox(f"There are no games to delete",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def addemu(self, event):
        # Adds a record to the list using current view
        #  'sdfsfsfsdfs': {'Application': 'DosBox', 'Options': 'stuff here sdsds'},
        #
        dlg = wx.TextEntryDialog(
            self, 'Name of the Emulator is?',
            'Add an emulator', '?')
        # dlg.SetValue("Python is the best!")
        if dlg.ShowModal() == wx.ID_OK:
            # self.log.WriteText('You entered: %s\n' % dlg.GetValue())
            emuname = dlg.GetValue()
            if emuname not in self.emulator:

                # self.games_dict['??'] = {'Application': emuname, 'Options': ''}
                # current_game = '??'
                dlg2 = wx.FileDialog(
                    self, message="Select the emulator's executable",
                    # defaultPath= os.getenv("USERPROFILE"),
                    defaultDir=self.game_lib,
                    style=wx.DD_DEFAULT_STYLE)

                # Show the dialog and retrieve the user response.
                if dlg2.ShowModal() == wx.ID_OK:
                    # load directory
                    path = dlg2.GetPath()
                    self.dosbox_loc = path
                    self.working_directory = dlg2.GetDirectory()
                else:
                    path = ''
                # Destroy the dialog.
                dlg2.Destroy()

                dlg3 = wx.DirDialog(
                    self, message="Select the emulator's default games directory",
                    # defaultPath= os.getenv("USERPROFILE"),
                    defaultPath=self.game_lib,
                    style=wx.DD_DEFAULT_STYLE)

                # Show the dialog and retrieve the user response.
                if dlg3.ShowModal() == wx.ID_OK:
                    # load directory
                    path2 = dlg3.GetPath()
                else:
                    path2 = ''
                # Destroy the dialog.
                dlg3.Destroy()

                dlg4 = wx.TextEntryDialog(
                    self, 'Any default option to add?',
                    'will be added to the option', '?')
                # dlg4.SetValue(self.default_option)
                self.default_option = dlg4.GetValue()
                if dlg4.ShowModal() == wx.ID_OK:
                    default_local = dlg4.GetValue()
                    dlg4.Destroy()
                else:
                    default_local = ""

                # Add the new emulator to the dictionary
                self.emu_dict[emuname] = {'Location': '"' + path + '"',
                                          'Library_default': path2,
                                          'Default_option': default_local,
                                          'Working_Directory': self.working_directory}
                self.game_lib = path2
                # Update the combo box to have the new emulator added and selected
                self.emulator = list(self.emu_dict.keys())
                self.choice_of_emu.Clear()
                self.emulator.sort()
                z = 0
                for y in self.emulator:
                    self.choice_of_emu.Append(y)
                    if y == emuname:
                        self.choice_of_emu.SetSelection(z)
                    z = z + 1
                self.choice_of_emu.Refresh()
                self.emulator_name = emuname
                self.filterthegames(True)
            else:
                wx.MessageBox(f"The emulator {emuname} is already setup",
                              "Warning",
                              wx.OK | wx.ICON_STOP | wx.CENTER)
        dlg.Destroy()

    def editemu(self, event):
        if len(self.emulator) > 0:
            emuselected_index = self.choice_of_emu.GetSelection()
            self.emulator_name = self.emulator[emuselected_index]
            dlg = wx.TextEntryDialog(
                self, 'Change the name of the emulator?',
                'Edit emulator', '?')
            dlg.SetValue(self.emulator_name)
            if dlg.ShowModal() == wx.ID_OK:
                # self.log.WriteText('You entered: %s\n' % dlg.GetValue())
                emulator_name_new = dlg.GetValue()
                # Ok to not change the name, so not check to see if it is already there
                x = self.emu_dict[self.emulator_name]["Location"]
                x = x.strip('"')
                dlg2 = wx.FileDialog(
                    self, message="Select the emulator's executable",
                    # defaultPath= os.getenv("USERPROFILE"),
                    defaultFile=x,
                    style=wx.DD_DEFAULT_STYLE)

                # Show the dialog and retrieve the user response.
                if dlg2.ShowModal() == wx.ID_OK:
                    # load directory
                    path = dlg2.GetPath()
                    self.dosbox_loc = path
                    self.working_directory = dlg2.GetDirectory()
                else:
                    path = ''
                # Destroy the dialog.
                dlg2.Destroy()

                dlg3 = wx.DirDialog(
                    self, message="Select the emulator's default games directory",
                    # defaultPath= os.getenv("USERPROFILE"),
                    defaultPath=self.game_lib,
                    style=wx.DD_DEFAULT_STYLE)

                # Show the dialog and retrieve the user response.
                if dlg3.ShowModal() == wx.ID_OK:
                    # load directory
                    path2 = dlg3.GetPath()
                else:
                    path2 = ''
                # Destroy the dialog.
                dlg3.Destroy()

                dlg4 = wx.TextEntryDialog(
                    self, 'Any default option to add?',
                    'will be added to the option', '?')
                # dlg4.SetValue(self.default_option)
                self.default_option = dlg4.GetValue()
                if dlg4.ShowModal() == wx.ID_OK:
                    default_local = dlg4.GetValue()
                    dlg4.Destroy()
                else:
                    default_local = ""

                # Add the new emulator to the dictionary
                # Although the option is 'amend', it will delete and re-create it from emu dictionary
                # If you cancel selecting the file locations, they remain as before
                if not path:
                    path = self.emu_dict[self.emulator_name]["Location"]
                if not path2:
                    path2 = self.emu_dict[self.emulator_name]["Library_default"]
                self.game_lib = path2
                # Deletes the details with the old name
                del self.emu_dict[self.emulator_name]
                # Adds it with the new name
                self.emu_dict[emulator_name_new] = {'Location': path,
                                                    'Library_default': path2,
                                                    'Default_option': default_local,
                                                    'Working_Directory': self.working_directory}
                # emulator hold a list of the emulators, needs to be refreshed
                self.emulator = list(self.emu_dict.keys())
                # Uses the filtered list of games to change the relevant games dictionary to the new emulator name
                for x in self.filtered_game_list:
                    y = self.game_index_dict[x]
                    self.games_dict[y]["Application"] = emulator_name_new
                # Updates the comb box with the new list of emulator and selects the amended one
                self.choice_of_emu.Clear()
                self.emulator.sort()
                z = 0
                for y in self.emulator:
                    self.choice_of_emu.Append(y)
                    if y == emulator_name_new:
                        self.choice_of_emu.SetSelection(z)
                    z = z + 1
                self.choice_of_emu.Refresh()
                self.emulator_name = emulator_name_new
                self.filterthegames(True)
            dlg.Destroy()
        else:
            wx.MessageBox(f"Add emulator to edit",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def deleteemu(self, event):

        # Test to check this is not the last emulator
        if len(self.emulator) > 0:
            emuselected_index = self.choice_of_emu.GetSelection()
            self.emulator_name = self.emulator[emuselected_index]

            dlg = wx.MessageDialog(self, f'Do you really want to delete {self.emulator_name}',
                                   'Are you sure? (all game set up info goes with it)',
                                   # wx.OK | wx.ICON_INFORMATION
                                   wx.OK | wx.CANCEL | wx.ICON_STOP
                                   )
            if dlg.ShowModal() == wx.ID_OK:
                # deletes the emulator from the emu dictionary
                del self.emu_dict[self.emulator_name]
                # Steps through the games and removes any related to the emulator from the dictionary
                for x in self.filtered_game_list:
                    y = self.game_index_dict[x]
                    del self.games_dict[y]
                # Updates the comb box with the list of emulators remaining
                self.choice_of_emu.Clear()
                self.emulator.remove(self.emulator_name)
                self.emulator.sort()
                for y in self.emulator:
                    self.choice_of_emu.Append(y)
                # picks the first emulator to refresh the screen
                if len(self.emulator) > 0:
                    self.choice_of_emu.SetSelection(0)
                    self.choice_of_emu.Refresh()
                    self.emulator_name = self.emulator[0]
                self.filterthegames(True)
            dlg.Destroy()
        else:
            wx.MessageBox("This is no emulator to delete..",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def onfileopen(self, event):
        # wx.MessageBox("Hello OnfileOpen")
        """Open a file"""
        # if wx.Platform == '__WXMSW__':
        #    path = os.getenv("USERPROFILE")
        # show dir dialog
        if len(self.filtered_game_list) > 0:
            select_index = self.my_list.GetSelection()
            self.current_game = self.choice_of_games[select_index]

            dlg = wx.FileDialog(
                self, message="Select game executable",
                # defaultPath= os.getenv("USERPROFILE"),
                defaultDir=self.game_lib,
                style=wx.DD_DEFAULT_STYLE)

            # Show the dialog and retrieve the user response.
            if dlg.ShowModal() == wx.ID_OK:
                # load directory
                path = dlg.GetPath()
                options_before = self.games_dict[self.current_game]["Options"]
                self.games_dict[self.current_game]["Options"] = options_before + ' "' + path + '" '
                self.on_clk(select_index)
            else:
                path = ''
                # Destroy the dialog.
                dlg.Destroy()
            # Update the options

            return path

        else:
            wx.MessageBox(f"There is no game setup",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def run_game(self, event):
        value = self.emu_location.GetValue()
        if len(self.filtered_game_list) > 0:
            select_index = self.my_list.GetSelection()
            #self.current_game = self.choice_of_games[select_index]
            self.listed_game = self.choice_of_games[select_index]
            self.current_game = self.game_index_dict[self.listed_game]
            doscmd = value + ' ' + self.games_dict[self.current_game]["Options"]
            # opt = self.games_dict[self.current_game]["Options"]
            # test = value + ',' + self.games_dict[current_game]["Options"]
            # subprocess.run([doscmd, '-conf', 'E:\\Dos\\dosboxconf\\doom2-0.74-3.conf', opt])
            # old method
            # subprocess.run(doscmd)
            # New method allows a change of working directory needed for application
            subprocess.Popen(doscmd, cwd=self.working_directory)
            # subprocess.run('"E:\\Program Files (x86)\\DOSBox-0.74-3\\DOSBox.exe"
            # -conf "E:\\Dos\\dosboxconf\\doom2-0.74-3.conf" "E:\Dos\DosGames\DOOM2\DOOM2.EXE"')
        else:
            wx.MessageBox(f"The emulator {value} hasn't got any games set up",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)

    def on_doubleclk(self, event):
        #select_index = self.my_list.GetSelection()
        #self.current_game = self.choice_of_games[select_index]
        #self.listed_game = self.choice_of_games[select_index]
        #self.current_game = self.game_index_dict[self.listed_game]

        #self.run_game(self.current_game)
        self.run_game(self.current_game)

    # Needs to be called if you want to change focus to a different game to update the screen
    def on_clk(self, event):
        select_index = self.my_list.GetSelection()
        #select_index = self.game_index_dict[select_index]

        self.listed_game = self.choice_of_games[select_index]
        self.current_game = self.game_index_dict[self.listed_game]


        # update items related to what has been selected
        # Update details for options
        # self.param_1_type.SetValue(self.games_dict[current_game]['Application'])
        self.runoptions.SetValue(self.games_dict[self.current_game]['Options'])
        self.gamenotes.SetValue(self.games_dict[self.current_game]['Notes'])
        #cmd = self.dosbox_loc + ' ' + self.games_dict[self.current_game]['Options']
        #self.cmdstring.SetValue(cmd)
        self.cmdstring.SetValue(self.dosbox_loc + ' ' + self.games_dict[self.current_game]['Options'])

    def filterchange(self, event):
        emuselected_index = self.choice_of_emu.GetSelection()
        self.emulator_name = self.emulator[emuselected_index]
        self.filterthegames(False)

    # This def needs to be called when the emulator or details about it change
    # It updates the global variables used
    def filterthegames(self, save_or_not):
        # Filter the main games list (only show games for this emulator)
        # What happens if nothing selected..
        # Identify which emulator is selected
        # select_index = self.my_list.GetSelection()
        # current_game = self.choice_of_games[select_index]
        # emuselected_index = self.choice_of_emu.GetSelection()
        # Only does anything if there is at least one emulator set up (Otherwise no point)
        if len(self.emulator) > 0:

            # If filterthegames was called with save_or_not being true we need to update the json files
            # saved to our profile.
            if save_or_not is True:
                # using indent=4 makes it more human readable
                with open(self.emu_file, 'w') as ef:
                    json.dump(self.emu_dict, ef, indent=4)
                with open(self.game_file, 'w') as gf:
                    json.dump(self.games_dict, gf, indent=4)
            emuselected_index = self.emulator.index(self.emulator_name)
            self.emulator_name = self.emulator[emuselected_index]

            # When the emulator is changed you need to update the dialogue and global variables used elsewhere
            self.emu_location.SetValue(self.emu_dict[self.emulator[emuselected_index]]['Location'])
            self.dosbox_loc = self.emu_dict[self.emulator[emuselected_index]]['Location']
            self.game_location.SetValue(self.emu_dict[self.emulator[emuselected_index]]['Library_default'])
            self.game_lib = self.emu_dict[self.emulator[emuselected_index]]['Library_default']
            self.default.SetValue(self.emu_dict[self.emulator[emuselected_index]]['Default_option'])
            self.default_option = self.emu_dict[self.emulator[emuselected_index]]['Default_option']
            self.cwd.SetValue(self.emu_dict[self.emulator[emuselected_index]]['Working_Directory'])
            self.working_directory = self.emu_dict[self.emulator[emuselected_index]]['Working_Directory']

            # Saving the data to disk

        else:
            self.emu_location.SetValue('')
            self.game_location.SetValue('')
            self.cmdstring.SetValue('')

        self.filtered_game_list = []
        self.game_index_dict = {}
        for x in self.games_dict.keys():
            if self.games_dict[x]['Application'] == self.emulator_name:
                self.filtered_game_list.append(self.games_dict[x]['Game'])
                self.game_index_dict.update({self.games_dict[x]['Game'] : x })
        self.filtered_game_list.sort()

        if self.current_game in self.filtered_game_list:
            current_selection = self.filtered_game_list.index(self.current_game)
        else:
            current_selection = 0
        self.choice_of_games = self.filtered_game_list
        self.my_list.Set(self.choice_of_games)

        # Assumption is that the first game on the list should be selected after calling this.
        # what happens if there is not one there??
        # self.on_clk(current_game)
        if len(self.filtered_game_list) > 0:
            self.my_list.SetSelection(current_selection)
            self.on_clk(self.current_game)
        else:
            self.runoptions.SetValue('')
            self.gamenotes.SetValue('')
            # cmd = dosbox_loc
            self.cmdstring.SetValue('')

    # ----------------------------------------------------------------------

    def onedit(self, event):
        # selectoption_before = self.games_dict[current_game]["Options"]
        if len(self.filtered_game_list) > 0:
            updated = self.runoptions.Value
            updatednotes = self.gamenotes.Value
            self.games_dict[self.current_game]["Options"] = updated
            self.games_dict[self.current_game]["Notes"] = updatednotes
            self.cmdstring.SetValue(self.dosbox_loc + ' ' + self.games_dict[self.current_game]['Options'])
            #self.filterthegames(True)
            #self.current_game = self.game_index_dict[self.current_game]
            dlg = wx.MessageDialog(self, f'Option updated for {self.listed_game}',
                                   'Done',
                                   # wx.OK | wx.ICON_INFORMATION
                                   wx.OK | wx.ICON_INFORMATION
                                   )
            if dlg.ShowModal() == wx.ID_OK:
                dlg.Destroy()
        else:
            wx.MessageBox("There are no games set up yet..",
                          "Warning",
                          wx.OK | wx.ICON_STOP | wx.CENTER)


def main():
    app = wx.App()
    MyFrame()
    app.MainLoop()


if __name__ == '__main__':
    main()
