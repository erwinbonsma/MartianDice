import { useState, useEffect } from 'react';
import Button from 'react-bootstrap/Button';

export function Chat(props) {
	const [messageInput, setMessageInput] = useState('');
	const [chatLog, setChatLog] = useState(Array.from({length: 20}, (_, index) =>
		[index, "Bob", `Message ${index}`]
	));

	const handleInputChange = (event) => {
		setMessageInput(event.target.value);
	};

	const onSendMessage = () => {
		props.websocket.send(JSON.stringify({
			action: "chat",
			game_id: props.roomId,
			message: messageInput
		}));

		setMessageInput('');
	}

	useEffect(() => {
		const onMessage = (event) => {
			const msg = JSON.parse(event.data);

			if (msg.type === "chat") {
				const chatEntry = [new Date(), msg.client_id, msg.message];
				setChatLog([...chatLog, chatEntry]);
				console.log("chatLog", chatLog);
			}
		};

		props.websocket.addEventListener('message', onMessage);

		return function cleanup() {
			props.websocket.removeEventListener('message', onMessage);
		}
	}, [props.websocket, chatLog]);

	// Not sure why flex for ChatMessageArea cannot be specified in style sheet
	return (
		<div className="Chat" style={{display: "flex", flexDirection: "column"}}>
			<h4 className="TableHeader">Chat</h4>
			<div className="ChatMessageArea" style={{flex: "1 1 0"}}>
				<ul className="ChatMessages">
					{ chatLog.map(([key, player, msg]) =>
						<li key={key}>{player}: {msg}</li>
					)}
				</ul>
			</div>
			<div className="TableRow">
				<input type="text" value={messageInput} onChange={handleInputChange} style={{fontSize: "small"}}/>
				<Button onClick={onSendMessage} disabled={messageInput === ''} sz="sm">Send</Button>
			</div>
		</div>
	)
}