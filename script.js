// Theme toggling
function toggleTheme() {
    const body = document.body;
    const themeToggle = document.getElementById('theme_toggle');
    const currentTheme = body.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        body.removeAttribute('data-theme');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i><span>Dark Mode</span>';
        localStorage.setItem('theme', 'light');
    } else {
        body.setAttribute('data-theme', 'dark');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i><span>Light Mode</span>';
        localStorage.setItem('theme', 'dark');
    }
}

// Apply saved theme on load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    const themeToggle = document.getElementById('theme_toggle');
    
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i><span>Light Mode</span>';
    }
});

// Auto-resize textarea
const textarea = document.getElementById("user_input");
textarea.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight < 120 ? this.scrollHeight : 120) + "px";
});

// Handle Enter key
textarea.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Function to format AI responses with better styling
function formatResponse(text) {
    // Convert markdown-like syntax to HTML
    let formatted = text
        // Handle headers with double asterisks
        .replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        
        // Handle lists (assumes lines starting with * or - or numbers)
        .replace(/^\s*[\*\-]\s+(.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
        
        // Handle numbered lists
        .replace(/^\s*(\d+\.\s+)(.+)$/gm, '<li>$2</li>')
        .replace(/(<li>.*<\/li>)/gs, function(match) {
            if (!/^<ul>/.test(match)) return '<ol>' + match + '</ol>';
            return match;
        })
        
        // Handle paragraphs (lines separated by two newlines)
        .replace(/\n\s*\n/g, '</p><p>')
        
        // Preserve emoji
        .replace(/[\u{1F600}-\u{1F64F}|\u{1F300}-\u{1F5FF}|\u{1F680}-\u{1F6FF}|\u{2600}-\u{26FF}|\u{2700}-\u{27BF}|\u{1F900}-\u{1F9FF}|\u{1F1E0}-\u{1F1FF}|\u{1F200}-\u{1F2FF}|\u{1F700}-\u{1F77F}|\u{1F780}-\u{1F7FF}|\u{1F800}-\u{1F8FF}|\u{1F900}-\u{1F9FF}|\u{1FA00}-\u{1FA6F}|\u{1FA70}-\u{1FAFF}]/gu, match => match);
    
    // Handle tables
    if (text.includes('|')) {
        const tableLines = text.split('\n').filter(line => line.includes('|'));
        if (tableLines.length > 2) {
            let tableHtml = '<table class="study-table">';
            // Process header
            let headerRow = tableLines[0];
            tableHtml += '<thead><tr>';
            headerRow.split('|').filter(cell => cell.trim() !== '').forEach(cell => {
                tableHtml += `<th>${cell.trim()}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            
            // Skip separator row (line 1) and process data rows
            for (let i = 2; i < tableLines.length; i++) {
                tableHtml += '<tr>';
                tableLines[i].split('|').filter(cell => cell.trim() !== '').forEach(cell => {
                    tableHtml += `<td>${cell.trim()}</td>`;
                });
                tableHtml += '</tr>';
            }
            tableHtml += '</tbody></table>';
            
            // Replace the original table text with HTML table
            formatted = formatted.replace(/\|[\s\S]*?\n\s*\n/g, tableHtml);
        }
    }
    
    // Wrap in paragraph tags if not already wrapped
    if (!formatted.startsWith('<')) {
        formatted = '<p>' + formatted + '</p>';
    }
    
    return formatted;
}

function saveChat() {
    const chatBox = document.getElementById("chat_output");
    const chatMessages = chatBox.innerHTML;
    
    // Create a chat session object
    const session = {
        id: Date.now(),
        date: new Date().toLocaleString(),
        title: generateChatTitle(),
        content: chatMessages
    };
    
    // Get existing sessions or initialize empty array
    let sessions = JSON.parse(localStorage.getItem('chatSessions')) || [];
    
    // Add new session
    sessions.push(session);
    
    // Save back to local storage
    localStorage.setItem('chatSessions', JSON.stringify(sessions));
    
    // Update history sidebar if it exists
    updateHistorySidebar();
    
    return session.id;
}

// Generate a title based on the first few messages
function generateChatTitle() {
    const chatBox = document.getElementById("chat_output");
    const messages = chatBox.querySelectorAll('.user-message');
    
    if (messages.length > 0) {
        // Use the first user message as the title (limited to 30 chars)
        const firstMessage = messages[0].textContent.replace('You', '').trim();
        return firstMessage.length > 30 ? 
            firstMessage.substring(0, 30) + '...' : 
            firstMessage;
    }
    
    return 'Chat session ' + new Date().toLocaleString();
}

// Function to load a saved chat
function loadChat(sessionId) {
    const sessions = JSON.parse(localStorage.getItem('chatSessions')) || [];
    const session = sessions.find(s => s.id === parseInt(sessionId));
    
    if (session) {
        const chatBox = document.getElementById("chat_output");
        chatBox.innerHTML = session.content;
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
        
        // Close the sidebar on mobile after selecting a chat
        if (window.innerWidth < 768) {
            toggleHistorySidebar();
        }
    }
}

// Function to delete a saved chat
function deleteChat(sessionId, event) {
    // Prevent the click from bubbling to the parent (which would load the chat)
    event.stopPropagation();
    
    if (confirm('Are you sure you want to delete this chat?')) {
        let sessions = JSON.parse(localStorage.getItem('chatSessions')) || [];
        sessions = sessions.filter(s => s.id !== parseInt(sessionId));
        localStorage.setItem('chatSessions', JSON.stringify(sessions));
        
        // Update history sidebar
        updateHistorySidebar();
    }
}

// Function to toggle history sidebar
function toggleHistorySidebar() {
    const sidebar = document.getElementById("history_sidebar");
    sidebar.classList.toggle("open");
    
    // Update the button icon
    const button = document.getElementById("history_toggle");
    if (sidebar.classList.contains("open")) {
        button.innerHTML = '<i class="fas fa-times"></i>';
    } else {
        button.innerHTML = '<i class="fas fa-history"></i>';
    }
    
    // If opening the sidebar, update it
    if (sidebar.classList.contains("open")) {
        updateHistorySidebar();
    }
}

// Function to update history sidebar with saved chats
function updateHistorySidebar() {
    const sidebar = document.getElementById("history_sidebar");
    if (!sidebar) return;
    
    const historyList = document.getElementById("history_list");
    const sessions = JSON.parse(localStorage.getItem('chatSessions')) || [];
    
    // Sort sessions by date (newest first)
    sessions.sort((a, b) => b.id - a.id);
    
    // Clear current list
    historyList.innerHTML = '';
    
    if (sessions.length === 0) {
        historyList.innerHTML = '<div class="empty-history">No saved chats yet</div>';
        return;
    }
    
    // Add each session to the list
    sessions.forEach(session => {
        const sessionEl = document.createElement('div');
        sessionEl.className = 'history-item';
        sessionEl.dataset.id = session.id;
        sessionEl.onclick = () => loadChat(session.id);
        
        sessionEl.innerHTML = `
            <div class="history-title">${session.title}</div>
            <div class="history-date">${session.date}</div>
            <button class="delete-history" onclick="deleteChat(${session.id}, event)">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        historyList.appendChild(sessionEl);
    });
}

async function sendMessage() {
    const userInput = document.getElementById("user_input").value.trim();
    if (!userInput) return;

    const chatBox = document.getElementById("chat_output");
    
    // Add user message
    chatBox.innerHTML += `
        <div class="message user-message">
            <div class="message-label">You</div>
            ${userInput}
        </div>
    `;
    
    // Reset textarea
    document.getElementById("user_input").value = "";
    textarea.style.height = "auto";
    
    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Show typing indicator
    document.getElementById("typing_indicator").style.display = "block";

    try {
        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userInput })
        });

        // Hide typing indicator
        document.getElementById("typing_indicator").style.display = "none";
        
        const data = await response.json();
        if (data.response) {
            // Format the response using markdown
            const formattedResponse = formatResponse(data.response);
            
            chatBox.innerHTML += `
                <div class="message ai-message">
                    <div class="message-label">AI Tutor</div>
                    <div class="formatted-content">${formattedResponse}</div>
                </div>
            `;
        } else {
            chatBox.innerHTML += `
                <div class="message ai-message">
                    <div class="message-label">Error</div>
                    ${data.error || "Something went wrong."}
                </div>
            `;
        }
    } catch (error) {
        // Hide typing indicator
        document.getElementById("typing_indicator").style.display = "none";
        
        chatBox.innerHTML += `
            <div class="message ai-message">
                <div class="message-label">Error</div>
                Failed to connect to server. Please check if the Flask application is running.
            </div>
        `;
    }
    
    // Scroll to bottom again
    chatBox.scrollTop = chatBox.scrollHeight;
    saveChat();
}

document.addEventListener('DOMContentLoaded', () => {
    // Your existing code here
    
    // Create new chat button functionality
    const newChatBtn = document.getElementById("new_chat");
    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => {
            // Save current chat before creating new one
            if (document.querySelectorAll('#chat_output .message').length > 1) {
                saveChat();
            }
            
            // Clear chat box
            const chatBox = document.getElementById("chat_output");
            chatBox.innerHTML = `
                <div class="message ai-message">
                    <div class="message-label">AI Tutor</div>
                    <div class="formatted-content"><p>Hi there! I'm your AI study assistant. How can I help you with your learning today?</p></div>
                </div>
            `;
            
            // Close sidebar on mobile
            if (window.innerWidth < 768 && document.getElementById("history_sidebar").classList.contains("open")) {
                toggleHistorySidebar();
            }
        });
    }
});