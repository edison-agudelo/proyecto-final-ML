let modal = null;
let video = null;
let canvas = null;
let imagenInput = null;

document.addEventListener("DOMContentLoaded", () => {
    modal = document.getElementById("cameraModal");
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    imagenInput = document.getElementById("imagen");

    const snapBtn = document.getElementById("snap");
    const closeBtn = document.getElementById("closeModal");

    // 📸 Botón de tomar foto
    snapBtn.addEventListener("click", () => {
        const context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataURL = canvas.toDataURL("image/png");
        document.getElementById("captured").src = dataURL;

        // Guardar imagen para enviarla al backend
        imagenInput.value = dataURL;
    });

    // ❌ Botón cerrar modal
    closeBtn.addEventListener("click", cerrarCamara);
});

// ==========================================================
// 🔹 FUNCIÓN PARA INICIAR CÁMARA
// ==========================================================
function iniciarCamara() {
    modal.style.display = "flex";

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.play();
        })
        .catch(error => {
            alert("⚠️ Error al acceder a la cámara: " + error);
        });
}

// ==========================================================
// 🔹 FUNCIÓN PARA CERRAR CÁMARA
// ==========================================================
function cerrarCamara() {
    modal.style.display = "none";

    // Detener la cámara
    if (video.srcObject) {
        let tracks = video.srcObject.getTracks();
        tracks.forEach(track => track.stop());
    }
}
