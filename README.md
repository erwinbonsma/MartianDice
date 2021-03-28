# Martian Dice

Online multi-player version of dice game [Martian Dice](https://boardgamegeek.com/boardgame/99875/martian-dice).

![Martian Dice screenshot](MartianDice-Screenshot.png)

Play the game on [my website](https://bonsma.home.xs4all.nl/Games/MartianDice/index.html).

## Features

* Play against other players
* Play against bots: Random, Defensive, Aggressive, and Smart
* Basic animations
* Basic sound-effects
* Responsive UI: play on phones, tablets or monitors
* Chat function
* Graceful disconnection handling:
	* Disconnected players can rejoin
	* Forcefully end turns of non-responsive players

## Technologies

Front-end:
* HTML5/CSS
* Javascript
* ReactJS + React Bootstrap

Back-end:
* Python
* Websocket communication
* AWS
	* Lambda services
	* DynamDb storage
	* Deployment via CDK

## Credits

* Game Design: Scott Almes
* Coding: Erwin Bonsma
* Graphics: Erwin Bonsma
* Sound-effects (all from [freesound.org](https://freesound.org)):
	* Cow ([cow.mp3](https://freesound.org/people/Benboncan/sounds/58277/)) by Benboncan
	* Chicken ([kip.mp3](https://freesound.org/people/Rudmer_Rotteveel/sounds/316920/)) by Rudmer_Rotteveel
	* Human ([huh.mp3](https://freesound.org/people/davdud101/sounds/150505/)) by davdud101
	* Ray ([ray.mp3](https://freesound.org/people/peepholecircus/sounds/171705/)) by peepholecircus
	* UFO ([ufo.mp3](https://freesound.org/people/plasterbrain/sounds/395500/)) by plasterbrain
	* Abduction ([win.mp3](https://freesound.org/people/TiesWijnen/sounds/518096/)) by TiesWijnen
	* Defeat ([die.mp3](https://freesound.org/people/josepharaoh99/sounds/364929/)) by josepharaoh99
