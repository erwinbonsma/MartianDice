import { useEffect, useState } from 'react';

// audioTracks: A dictionary with Audio values and string IDs as key.
export function AudioPlayer({ audioTracks, playTrack }) {
	// Tracks the last request. Only a change of request will initiate a new play
	const [ lastRequest, setLastRequest ] = useState();
	const [ isPlaying, setIsPlaying ] = useState({});

	// Initialise track-related state
	useEffect(() => {
		setIsPlaying(
			Object.keys(audioTracks).reduce(
				(dict, key) => {
					dict[key] = false;
					return dict;
				}, {})
		);
	}, [audioTracks]);

	// Add listeners for track completion
	useEffect(() => {
		const listeners = Object.keys(audioTracks).map(key => {
			return () => {
				const newPlaying = { ...isPlaying };
				newPlaying[key] = false;
				setIsPlaying(newPlaying);
			}
		});

		Object.entries(audioTracks).forEach(([key, audio]) => {
			audio.addEventListener('ended', listeners[key]);
		});

		return function cleanup() {
			Object.entries(audioTracks).forEach(([key, audio]) => {
				audio.removeEventListener('ended', listeners[key]);
			});	
		};
	}, [audioTracks, isPlaying]);

	// Handle requests
	useEffect(() => {
		if (playTrack !== lastRequest) {
			const newPlaying = { ...isPlaying };
			if (playTrack) {
				newPlaying[playTrack] = true;
			}
			if (lastRequest) {
				newPlaying[lastRequest] = false;
			}
			setIsPlaying(newPlaying);

			setLastRequest(playTrack);
		}
	}, [playTrack, lastRequest, isPlaying]);

	// Actually play the sounds
	useEffect(() => {
		Object.entries(audioTracks).forEach(([key, audio]) => {
			if (isPlaying[key]) {
				audio.play();
			}
		})
	}, [isPlaying, audioTracks]);

	// Component is invisible
	return null;
}