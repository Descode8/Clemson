document.addEventListener('DOMContentLoaded', function() {
    // Display an initial message when the chat box first appears
    const chatBox = document.getElementById('chat-box');
    const initialMessage = document.createElement('div');
    initialMessage.className = 'message bot-message';
    initialMessage.textContent = 'Let\'s learn some Web Dev 🚀';
    chatBox.appendChild(initialMessage);

    // Event listener for the Enter key in the input field
    const userInputField = document.getElementById('user-input');
    userInputField.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent the default action to avoid form submission
            sendMessage();
        }
    });

    // Event listener for the Send button
    document.getElementById('send-btn').addEventListener('click', sendMessage);
});

function sendMessage() {
    const userInputField = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');
    const userInput = userInputField.value;

    // Change the send button icon to light blue while sending the message
    sendButton.src = 'static/Images/purple_button.png';

    // Disable hover effect while fetching response
    sendButton.classList.add('no-hover');

    if (userInput.trim() === '') {
        return; // Don't send an empty message
    }

    // Disable input and send button
    userInputField.disabled = true;
    sendButton.disabled = true;

    // Append user's message
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);
    userInputField.value = ''; // Clear the input box after sending the message

    // Insert a placeholder for the loading animation
    const loadingPlaceholder = document.createElement('div');
    loadingPlaceholder.className = 'loading-placeholder';
    chatBox.appendChild(loadingPlaceholder);

    // Display the loading wheel
    loadingPlaceholder.innerHTML = '<span class="running-dots"></span>';

    // Adjust scroll for the loading wheel
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json())
    .then(data => {
        // Create a new div for the AI's response
        let aiResponse = document.createElement('div');
        aiResponse.className = 'message bot-message';

        // Customize marked renderer to add target="_blank" to links
        const renderer = new marked.Renderer();
        renderer.link = function(href, title, text) {
            return `<a href="${href}" target="_blank">${text}</a>`;
        };

        // Use marked to parse the Markdown response into HTML
        let formattedResponse = marked.parse(data.response, { renderer: renderer });
        aiResponse.innerHTML = formattedResponse;

        // Remove the loading placeholder and append AI's response
        loadingPlaceholder.remove();
        chatBox.appendChild(aiResponse);

        // Scroll to the bottom of the chat box after appending messages
        chatBox.scrollTop = chatBox.scrollHeight;
        
        // Change back to dark blue send button
        sendButton.src = 'static/Images/orange_button.png';
    })
    .catch(error => {
        console.error('Error:', error);
        loadingPlaceholder.remove(); // Remove the loading placeholder in case of error
        const errorMessage = document.createElement('div');
        errorMessage.className = 'message bot-message';
        errorMessage.textContent = 'Error generating response. Please try again later.';
        chatBox.appendChild(errorMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .finally(() => {
        userInputField.disabled = false;
        sendButton.disabled = false;
        sendButton.classList.remove('no-hover');
        userInputField.focus(); // Optionally, refocus the input field
    });
}
