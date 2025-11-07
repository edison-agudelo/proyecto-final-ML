let video = document.getElementById("video");
let foto = document.getElementById("foto");
let tomar = document.getElementById("tomar");
let enviar = document.getElementById("enviar");
let output = document.getElementById("output");
let selector = document.getElementById("listaCamaras");

navigator.mediaDevices.enumerateDevices().then(dispositivos => {
    dispositivos.forEach(d => {
        if (d.kind === "videoinput") {
            let opcion = document.createElement("option");
            opcion.value = d.deviceId;
            opcion.text = d.label || "Cámara " + (selector.length + 1);
            selector.appendChild(opcion);
        }
    });
    iniciarCamara(selector.value);
});

selector.onchange = () => iniciarCamara(selector.value);

function iniciarCamara(deviceId) {
    navigator.mediaDevices.getUserMedia({
        video: { deviceId: { exact: deviceId } }
    }).then(stream => {
        video.srcObject = stream;
        video.play();
    }).catch(err => {
        alert("Error al acceder a la cámara: " + err);
    });
}

tomar.onclick = () => {
    let canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 128;
    canvas.getContext("2d").drawImage(video, 0, 0, 128, 128);
    foto.src = canvas.toDataURL("image/png");
};

enviar.onclick = () => {
    fetch("/calidad", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imagen: foto.src })
    })
    .then(res => res.json())
    .then(data => {
        output.innerHTML = `<h2>${data.resultado}</h2>`;
    });
};
