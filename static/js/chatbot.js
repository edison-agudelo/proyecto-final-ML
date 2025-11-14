document.addEventListener("DOMContentLoaded", () => {
    const widget = document.getElementById("chatbot-widget");
    const toggleBtn = document.getElementById("chatbot-toggle");
    const closeBtn = document.getElementById("chatbot-close");
    const msgContainer = document.getElementById("chatbot-messages");
    const input = document.getElementById("chatbot-input");
    const sendBtn = document.getElementById("chatbot-send");

    // Estado inicial: solo burbuja visible
    widget.style.display = "none";

    // Abrir / cerrar con la burbuja
    toggleBtn.addEventListener("click", () => {
        if (widget.style.display === "none") {
            widget.style.display = "flex";
            input.focus();
        } else {
            widget.style.display = "none";
        }
    });

    // Botón de cerrar en el cuadro
    closeBtn.addEventListener("click", () => {
        widget.style.display = "none";
    });

    // Añadir mensaje al cuadro (no se guarda en BD, solo en la página)
    function addMessage(text, from) {
        const div = document.createElement("div");
        div.classList.add("chat-message", from === "user" ? "user" : "bot");
        div.textContent = text;
        msgContainer.appendChild(div);
        msgContainer.scrollTop = msgContainer.scrollHeight;
    }

    // Enviar mensaje al backend
    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        addMessage("tú: " + text, "user");
        input.value = "";

        try {
            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mensaje: text })
            });

            const data = await resp.json();
            addMessage("bot: " + (data.respuesta || "No entendí bien 😅"), "bot");
        } catch (err) {
            console.error(err);
            addMessage("bot: Hubo un error al conectar con el servidor 😢", "bot");
        }
    }

    // Click en "Enviar"
    sendBtn.addEventListener("click", sendMessage);

    // Enter en el input
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

    // Mensaje inicial del bot
    addMessage("bot: ¡Hola! 👋 Soy el asistente del Puré Inteligente. ¿En qué puedo ayudarte hoy?", "bot");
});
