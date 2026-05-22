async function sendMessage() {
const input = document.getElementById("input");
const text = input.value.trim();
if (!text) return;

```
addMessage(text, "user");
input.value = "";

showTyping(true);

const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
});

const data = await res.json();

showTyping(false);
addMessage(data.response, "ai");
```

}

function addMessage(text, sender) {
const box = document.getElementById("chatBox");

```
const div = document.createElement("div");
div.className = "msg " + sender;
div.innerText = text;

box.appendChild(div);
box.scrollTop = box.scrollHeight;
```

}

function showTyping(state) {
document.getElementById("typing").style.display = state ? "block" : "none";
}

function newChat() {
fetch("/new_chat").then(() => location.reload());
}

function logout() {
window.location.href = "/logout";
}

function toggleTheme() {
document.body.classList.toggle("light");
}
