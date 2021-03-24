import { useEffect, useState } from 'react';

export function AudioPlayer({ tracks, playTrack }) {
	// Tracks the last request. Only a change of request will initiate a new play
	const [ lastRequest, setLastRequest ] = useState();
	const [ sources, setSources ] = useState({});
	const [ isPlaying, setIsPlaying ] = useState({});

	// Initialise track-related state
	useEffect(() => {
		setSources(
			Object.entries(tracks).reduce(
				(dict, [key, url]) => {
					dict[key] = new Audio(url);
					return dict;
				}, {})
		);

		setIsPlaying(
			Object.keys(tracks).reduce(
				(dict, key) => {
					dict[key] = false;
					return dict;
				}, {})
		);
	}, [tracks]);

	// Add listeners for track completion
	useEffect(() => {
		const listeners = Object.keys(sources).map(key => {
			const newPlaying = { ...isPlaying };
			newPlaying[key] = false;
			setIsPlaying(newPlaying);
		});

		Object.entries(sources).forEach(([key, audio]) => {
			audio.addEventListener('ended', listeners[key]);
		});

		return function cleanup() {
			Object.entries(sources).forEach(([key, audio]) => {
				audio.removeEventListener('ended', listeners[key]);
			});	
		};
	}, [sources]);

	// Handle requests
	useEffect(() => {
		if (playTrack != lastRequest) {
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
	})

	// Actually play the sounds
	useEffect(() => {
		Object.entries(isPlaying).forEach(([key, value]) => {
			console.log(`Track ${key} is ${value ? '' : 'not '}playing`)
		});
		Object.entries(sources).forEach(([key, audio]) => {
			if (isPlaying[key]) {
				audio.play();
			}
		})
	}, [isPlaying, sources]);

	// Component is invisible
	return null;
}