export function isDictionaryEmpty(dict) {
	// eslint-disable-next-line
	for (let key of Object.keys(dict)) {
		return false;
	}

	return true;
}

export function applyDieDelta(dict, die, delta) {
	const newDict = { ...dict };
	newDict[die] = (newDict[die] || 0) + delta;

	return newDict;
}

export function shuffle(l) {
	for (let i = l.length; --i > 0; ) {
		const j = Math.floor(Math.random() * (i + 1));
		const tmp = l[i];
		l[i] = l[j];
		l[j] = tmp;
	}
}
