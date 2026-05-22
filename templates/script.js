// Kazi ya kubonyeza kitufe cha Tuma au kubonyeza "Enter" kwenye keyboard
document.getElementById("sendBtn").addEventListener("click", sendMessage);
document.getElementById("userInput").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// Kazi kuu ya kutuma na kuonyesha ujumbe kwenye screen
function sendMessage() {
    let inputField = document.getElementById("userInput");
    let messageText = inputField.value.trim();

    // Kama mtumiaji hajaandika kitu, usitume
    if (messageText === "") return;

    // 1. Onyesha ujumbe wa mtumiaji kwenye chat box
    appendMessage(messageText, "user-message");

    // Futa maandishi kwenye sehemu ya kuandikia
    inputField.value = "";

    // 2. Weka jibu la mfano (Placeholder) wakati tunasubiri kuunganisha Flask wiki ijayo
    setTimeout(() => {
        appendMessage("Asante kwa ujumbe wako! Kwenye Week 2 & 3, nitaunganishwa na AI ili kukupa majibu sahihi kulingana na fomula yetu.", "ai-message");
    }, 1000);
}

// Kazi ya kuweka maswali ya haraka kutoka kwenye Quick Buttons
function quickQuestion(questionText) {
    document.getElementById("userInput").value = questionText;
    sendMessage();
}

// Kazi ya kuongeza ujumbe mpya kwenye chat box (HTML)
function appendMessage(text, senderClass) {
    let chatBox = document.getElementById("chatBox");
    
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("message", senderClass);
    messageDiv.innerText = text;
    
    chatBox.appendChild(messageDiv);
    
    // Kila ujumbe mpya ukiingia, screen ishuke chini yenyewe (Auto-scroll)
    chatBox.scrollTop = chatBox.scrollHeight;
}
