import { useState, useEffect, useRef } from 'react';
import Button from 'react-bootstrap/Button';

export function Chat({ roomId, websocket }) {
	const [messageInput, setMessageInput] = useState('');
	const [chatLog, setChatLog] = useState([]);

	const lastKey = chatLog.length && chatLog[chatLog.length - 1][0];
	const lastChatEntryRef = useRef(null);

	const handleInputChange = (event) => {
		setMessageInput(event.target.value);
	};

	const onSendMessage = (e) => {
		e.preventDefault();
		websocket.send(JSON.stringify({
			action: "chat",
			room_id: roomId,
			message: messageInput
		}));

		setMessageInput('');
	}

	useEffect(() => {
		lastChatEntryRef.current?.scrollIntoView({ behavior: "smooth" })
	}, [chatLog]);

	useEffect(() => {
		const onMessage = (event) => {
			const msg = JSON.parse(event.data);

			if (msg.type === "chat") {
				const chatEntry = [new Date(), msg.client_id, msg.message];
				setChatLog([...chatLog, chatEntry]);
			}
		};

		websocket.addEventListener('message', onMessage);

		return function cleanup() {
			websocket.removeEventListener('message', onMessage);
		}
	}, [websocket, chatLog]);

	// Not sure why flex for ChatMessageArea cannot be specified in style sheet
	return (
		<div className="Chat" style={{display: "flex", flexDirection: "column"}}>
			<h4 className="TableHeader">Chat</h4>
			<div className="ChatMessageArea" style={{flex: "1 1 0"}}>
				<ul className="ChatMessages">
					{ chatLog.map(([key, player, msg]) =>
						key === lastKey
						? <li key={key} ref={lastChatEntryRef}>{player}: {msg}</li>
						: <li key={key}>{player}: {msg}</li>
					)}
				</ul>
			</div>
			<form className="TableBody" style={{display: "flex"}} onSubmit={onSendMessage}>
				<input type="text" value={messageInput} onChange={handleInputChange}
					style={{fontSize: "small", flex: "1 1 0", margin: "0.2em 0.6em 0.2em 0"}}/>
				<Button type="submit" variant="primary" disabled={messageInput === ''} sz="sm">Send</Button>
			</form>
		</div>
	)
}