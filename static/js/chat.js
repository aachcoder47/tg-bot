// Generate a unique client ID or retrieve from localStorage
let clientId = localStorage.getItem("chat_client_id");
if (!clientId) {
    clientId = crypto.randomUUID();
    localStorage.setItem("chat_client_id", clientId);
}

const chatWidget = document.getElementById('chat-widget');
const chatWindow = document.getElementById('chat-window');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
let ws;

function toggleChat() {
    chatWindow.classList.toggle('hidden');
    if (!chatWindow.classList.contains('hidden')) {
        // If opening and not connected, connect
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            connectWebSocket();
        }
        // Focus input
        setTimeout(() => chatInput.focus(), 300);
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("Connected to Chat Server");
        // Optional: Send a "ping" or "init" just to ensure the server knows we're here
        // ws.send(JSON.stringify({ type: "init" }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "message" || data.type === "admin_message") {
            appendMessage(data.content, "agent");
        }
    };

    ws.onclose = () => {
        console.log("Disconnected from Chat Server");
        // Optional: specific UI for disconnect
    };

    ws.onerror = (error) => {
        console.error("WebSocket Error:", error);
    };
}

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("Not connected to chat server. Please try closing and reopening the chat.");
        return;
    }

    // Append locally
    appendMessage(text, "user");
    
    // Send to server
    ws.send(JSON.stringify({ content: text }));
    
    chatInput.value = "";
}

function appendMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.innerText = text;
    chatMessages.appendChild(msgDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}
