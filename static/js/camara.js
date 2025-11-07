let video = document.getElementById("video");
let canvas = document.getElementById("canvas");
let capturedImg = document.getElementById("captured");
let imageField = document.getElementById("imagen");
let cameraSelect = document.getElementById("cameraSelect");
let currentStream;

// Listar cámaras disponibles
async function listarCamaras() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    cameraSelect.innerHTML = ""; // limpiar lista

    devices.forEach(device => {
        if (device.kind === "videoinput") {
            let option = document.createElement("option");
            option.value = device.deviceId;
            option.text = device.label || `Cámara ${cameraSelect.length + 1}`;
            cameraSelect.appendChild(option);
        }
    });

    iniciarCamara();
}

// Iniciar cámara seleccionada
async function iniciarCamara() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }

    let cameraId = cameraSelect.value;

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({
            video: { deviceId: cameraId ? { exact: cameraId } : undefined }
        });

        video.srcObject = currentStream;
    } catch (error) {
        alert("⚠ Error al acceder a la cámara: " + error.message);
    }
}

// Tomar foto
document.getElementById("snap").addEventListener("click", function () {
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    let imageData = canvas.toDataURL("image/png");
    capturedImg.src = imageData;
    imageField.value = imageData; // Se envía al backend
});

// Cambiar cámara cuando el usuario selecciona otra
cameraSelect.addEventListener("change", iniciarCamara);

// Iniciar todo
navigator.mediaDevices.getUserMedia({ video: true })
    .then(listarCamaras)
    .catch(err => alert("No se pudo acceder a la cámara: " + err.message));

