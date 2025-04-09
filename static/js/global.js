function comprobarPermisos(tipo){
    //Comprobar permisos de voz
    if(tipo == 'microfono'){
        navigator.permissions.query({ name: 'microphone' })
        .then(function(permissionStatus) {
            console.log('Estado del permiso del micrófono:', permissionStatus.state);

            accionarPermisos(permissionStatus.state);
            /*if (permissionStatus.state === 'granted') {
                console.log('Acceso al micrófono');

            } else if (permissionStatus.state === 'prompt') {
                Swal.fire({
                    //title:"Error",
                    title:"Para poder usar el asistente correctamente debe concederle permisos de acceso al microfono",
                    html: "<button class='btn btn-success' onclick='solicitarPermisos(\"microfono\")'>Solicitar acceso</button>",
                    icon:"info",
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
                //solicitarPermisos('microfono');
            } else if (permissionStatus.state === 'denied') {
                Swal.fire({
                    title:"Acceso al Microfono Denegado",
                    html:"<p>El acceso al microfono ha sido denegado por el usuario.</p><p><em>Por favor, proporcione acceso el microfono para usar el asistente.</em></p>",
                    icon:"error",
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
            }*/

            // Monitorea los cambios en el estado del permiso
            permissionStatus.onchange = function() {
                //location.reload();
                console.log(permissionStatus.state);
                accionarPermisos(permissionStatus.state);
            };
        })
        .catch(function(error) {
            console.error('Error al verificar el estado del permiso del micrófono:', error);
        });
        /*navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            // El usuario ha concedido el acceso al micrófono
            console.log("Acceso al micrófono concedido.");
        })
        .catch(function(err) {
            // El usuario ha denegado el acceso al micrófono o ha ocurrido un error
            console.error("Error al intentar acceder al micrófono:", err);
        });*/

    }
}

function accionarPermisos(estado){
    if (estado === 'granted') {
        Swal.close();
        console.log('Acceso al micrófono');

    } else if (estado === 'prompt') {
        Swal.fire({
            //title:"Error",
            title:"Para poder usar el asistente correctamente debe concederle permisos de acceso al micrófono.",
            html: "<button class='btn btn-success' onclick='solicitarPermisos(\"microfono\")'>Solicitar acceso</button>",
            icon:"info",
            showConfirmButton: false,
            allowOutsideClick: false
        });
        //solicitarPermisos('microfono');
    } else if (estado === 'denied') {
        Swal.fire({
            title:"Acceso al Microfono Denegado",
            html:"<p>El acceso al microfono ha sido denegado por el usuario.</p><p><em>Por favor, proporcione acceso el microfono para usar el asistente.</em></p>",
            icon:"error",
            showConfirmButton: false,
            allowOutsideClick: false
        });
    }
}

function solicitarPermisos(permiso){
    if(permiso == 'microfono'){
        navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            console.log('Permiso concedido. El micrófono está disponible.');
            // Aquí puedes hacer uso del stream de audio
            // Detén el stream si no lo necesitas inmediatamente
            Swal.close();
            stream.getTracks().forEach(track => track.stop());
        })
        .catch(function(error) {
            if (error.name === 'NotAllowedError') {
                Swal.fire({
                    title:"Acceso al Microfono Denegado",
                    html:"<p>El acceso al microfono ha sido denegado por el usuario.</p><p><em>Por favor, proporcione acceso el microfono para usar el asistente.</em></p>",
                    icon:"error",
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
            } else if (error.name === 'NotFoundError') {
                Swal.fire({
                    title:"Microfono no encontrado",
                    html:"<p>No se encontró ningún micrófono disponible.</p><p><em>Debe tener habilitado el microfono para usar el asistente.</em></p>",
                    icon:"error",
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
            } else {
                Swal.fire({
                    title:"Error de acceso al microfono",
                    html:"<p>No se pudo solicitar acceso al microfono.</p><p><em>Por favor, habilite el acceso al microfono manualmente para usar el asistente.</em></p>",
                    icon:"error",
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
                //console.error('Error al solicitar el acceso al micrófono:', error);
            }
        });
    }
}

function comprobarNavegador(navegador) {
    const userAgent = navigator.userAgent;

    switch(navegador){
        case "chrome":
            return /Chrome/.test(userAgent) && /Google Inc/.test(navigator.vendor);
        break;
        case "safari":
            return /Safari/.test(navigator.userAgent) && /Apple Computer/.test(navigator.vendor);
        break;
        case "edge":
            return /Edg/.test(navigator.userAgent); 
        break;
        case "opera":
            return /OPR/.test(navigator.userAgent) || /Opera/.test(navigator.userAgent);
        break;
    }
}
