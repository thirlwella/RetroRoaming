# RetroRoaming
A simple front end to bring together the launching of emulators to play your old games, written in Python using wxPython

I have a few really old games that I like to play occasionally using emulators. Mostly DosBox and Fuse. When I play them I have often forgotten where they are, how to run them correctly and what the keys are. This program was written to bring this information together in one place and launch the games via the application to the windows cmd prompt

It makes it easy to create the cmd line you need to run the game and allows you to keep some notes on each game. Written for Windows, it will store this information in the user profile under \AppData\Local\RetroRoaming in two json files one for the location of the emulators and the other for the list of all the games.

There are python dependencies on wx, os, subprocess and json for it to run
