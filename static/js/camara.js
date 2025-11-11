// =======================================================
// 🎥 CONTROL DE CÁMARA - Integrado con Modal (Versión mejorada)
// =======================================================

let video = null;
let canvas = null;
let capturedImg = null;
let imageField = null;
let cameraSelect = null;
let currentStream = null;
let modal = null;

// =======================================================
// Inicialización al cargar el DOM
// =======================================================
window.addEventListener("DOMContentLoaded", async () => {
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    capturedImg = document.getElementById("captured");
    imageField = document.getElementById("imagen");
    cameraSelect = document.getElementById("cameraSelect");
    modal = document.getElementById("cameraModal");

    // Botón para tomar foto
    const snapBtn = document.getElementById("snap");
    if (snapBtn) snapBtn.addEventListener("click", tomarFoto);

    // Botón para cerrar modal
    const closeBtn = document.getElementById("closeModal");
    if (closeBtn) closeBtn.addEventListener("click", cerrarModal);

    // Evento de cambio de cámara
    if (cameraSelect) cameraSelect.addEventListener("change", iniciarCamara);

    // Pedir permiso de cámara al iniciar (solo una vez)
    try {
        await navigator.mediaDevices.getUserMedia({ video: true });
        await listarCamaras();
    } catch (err) {
        alert("⚠ No se pudo acceder a la cámara: " + err.message);
    }
});

// =======================================================
// Listar cámaras disponibles
// =======================================================
async function listarCamaras() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        cameraSelect.innerHTML = "";

        let videoDevices = devices.filter(d => d.kind === "videoinput");

        if (videoDevices.length === 0) {
            alert("⚠ No se encontraron cámaras disponibles.");
            return;
        }

        videoDevices.forEach((device, index) => {
            let option = document.createElement("option");
            option.value = device.deviceId;
            option.text = device.label || `Cámara ${index + 1}`;
            cameraSelect.appendChild(option);
        });

    } catch (err) {
        alert("⚠ No se pudieron listar las cámaras: " + err.message);
    }
}

// =======================================================
// Iniciar cámara seleccionada y mostrar modal
// =======================================================
async function iniciarCamara() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }

    if (!modal) modal = document.getElementById("cameraModal");
    modal.style.display = "flex";

    const cameraId = cameraSelect.value || undefined;

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({
            video: { deviceId: cameraId ? { exact: cameraId } : undefined }
        });

        video.srcObject = currentStream;
    } catch (error) {
        alert("⚠ Error al acceder a la cámara: " + error.message);
        cerrarModal();
    }
}

// =======================================================
// Tomar la foto y enviar al backend
// =======================================================
function tomarFoto() {
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    let imageData = canvas.toDataURL("image/png");
    capturedImg.src = imageData;
    imageField.value = imageData;
    cerrarModal();
}

// =======================================================
// Cerrar modal y detener la cámara
// =======================================================
function cerrarModal() {
    if (modal) modal.style.display = "none";

    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}
