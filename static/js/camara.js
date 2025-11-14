let video = null;
let canvas = null;
let cameraModal = null;
let imagenInput = null;

window.onload = function () {
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    cameraModal = document.getElementById("cameraModal");
    imagenInput = document.getElementById("imagen");

    document.getElementById("snap").onclick = tomarFoto;
    document.getElementById("closeModal").onclick = cerrarCamara;
};

// Abrir la cámara
function iniciarCamara() {
    cameraModal.style.display = "block";

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(err => {
            alert("No se pudo acceder a la cámara: " + err);
        });
}

// Tomar foto y mostrarla + convertir a base64
function tomarFoto() {
    let ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    let dataURL = canvas.toDataURL("image/png");

    // Mostrar preview
    document.getElementById("captured").src = dataURL;

    // Guardar base64 en input oculto
    imagenInput.value = dataURL;

    cerrarCamara();
}

// Cerrar modal de cámara
function cerrarCamara() {
    cameraModal.style.display = "none";

    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
}
