const Desklet = imports.ui.desklet;
const St = imports.gi.St;
const GLib = imports.gi.GLib;
const Gio = imports.gi.Gio;
const ByteArray = imports.byteArray;

const BACKEND_TIMEOUT_MS = 180000;

function TutorEscolarDesklet(metadata, desklet_id) {
    this._init(metadata, desklet_id);
}

TutorEscolarDesklet.prototype = {
    __proto__: Desklet.Desklet.prototype,

    _init: function(metadata, desklet_id) {
        Desklet.Desklet.prototype._init.call(this, metadata, desklet_id);
        this.uuid = metadata.uuid;
        this.deskletPath = GLib.get_user_data_dir() + "/cinnamon/desklets/" + this.uuid;

        this.window = new St.BoxLayout({
            vertical: true,
            style: "background-color: rgba(40, 44, 52, 0.92); border: 2px solid #4B5563; border-radius: 12px; padding: 15px; width: 360px;"
        });

        let titleBin = new St.Bin({ x_align: St.Align.MIDDLE });
        let titleLabel = new St.Label({
            text: "Mi Tutor Escolar Local",
            style: "font-size: 14px; font-weight: bold; color: #6EE7B7; padding-bottom: 8px;"
        });
        titleBin.set_child(titleLabel);
        this.window.add_actor(titleBin);

        this.responseLabel = new St.Label({
            text: "Hola! En que tarea te ayudo hoy?\nPuedo buscar en internet, resolver matematicas o leer archivos PDF/TXT.",
            style: "font-size: 11px; color: #E5E7EB; padding: 8px; background-color: rgba(0,0,0,0.2); border-radius: 6px;",
            line_wrap: true
        });

        let scrollBox = new St.ScrollView({
            height: 180,
            hscrollbar_policy: St.PolicyType.NEVER,
            vscrollbar_policy: St.PolicyType.AUTOMATIC
        });
        scrollBox.add_actor(this.responseLabel);
        this.window.add_actor(scrollBox);

        let inputContainer = new St.BoxLayout({ vertical: false, style: "padding-top: 10px;" });

        this.entry = new St.Entry({
            hint_text: "Escribe tu pregunta aqui...",
            style: "font-size: 11px; background-color: #374151; color: white; border: 1px solid #4B5563; border-radius: 6px; padding: 6px; width: 330px;"
        });

        this.entry.clutter_text.connect('activate', () => {
            this._enviarPreguntaAlBackend();
        });
        inputContainer.add_actor(this.entry);
        this.window.add_actor(inputContainer);

        this.setContent(this.window);
        this.setHeader("Tutor Escolar");
    },

    _enviarPreguntaAlBackend: function() {
        let textoUsuario = this.entry.get_text().trim();
        if (textoUsuario === "") return;
        this.entry.set_text("");
        this.responseLabel.set_text("Pensando tu respuesta...");

        let pythonScript = this.deskletPath + "/tutor_backend.py";
        let command = "python3 " + pythonScript;

        try {
            let datosEnvio = JSON.stringify({ "texto": textoUsuario });
            let [res, argv] = GLib.shell_parse_argv(command);
            let [success, pid, stdin_fd, stdout_fd, stderr_fd] =
                GLib.spawn_async_with_pipes(null, argv, null, GLib.SpawnFlags.SEARCH_PATH, null);

            if (success) {
                let timeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, BACKEND_TIMEOUT_MS, () => {
                    GLib.kill(pid, 15);
                    this.responseLabel.set_text("El tutor tardo demasiado. Revisa si llama-server esta corriendo.");
                    return GLib.SOURCE_REMOVE;
                });

                let outStream = new Gio.UnixOutputStream({ fd: stdin_fd, close_fd: true });
                outStream.write_all(datosEnvio + "\n", null);
                outStream.close(null);

                let inStream = new Gio.UnixInputStream({ fd: stdout_fd, close_fd: true });
                let dataReader = new Gio.DataInputStream({ base_stream: inStream });

                dataReader.read_line_async(GLib.PRIORITY_DEFAULT, null, (source, result) => {
                    if (timeoutId) {
                        GLib.source_remove(timeoutId);
                        timeoutId = null;
                    }

                    let [linea, length] = source.read_line_finish(result);
                    if (linea) {
                        try {
                            let lineaTexto = ByteArray.toString(linea);
                            let objetoRespuesta = JSON.parse(lineaTexto);
                            this.responseLabel.set_text(objetoRespuesta.respuesta);
                        } catch (e) {
                            this.responseLabel.set_text("Error al interpretar la respuesta del tutor.");
                        }
                    } else {
                        this.responseLabel.set_text("El tutor no pudo responder. Verifica si llama-server esta corriendo.");
                    }

                    inStream.close(null);
                    if (stderr_fd) {
                        new Gio.UnixInputStream({ fd: stderr_fd, close_fd: true }).close(null);
                    }
                });
            } else {
                if (stdin_fd) new Gio.UnixOutputStream({ fd: stdin_fd, close_fd: true }).close(null);
                if (stdout_fd) new Gio.UnixInputStream({ fd: stdout_fd, close_fd: true }).close(null);
                if (stderr_fd) new Gio.UnixInputStream({ fd: stderr_fd, close_fd: true }).close(null);
                this.responseLabel.set_text("No se pudo iniciar el motor del tutor escolar.");
            }
        } catch (err) {
            this.responseLabel.set_text("Error de conexion: " + err.message);
        }
    }
};

function main(metadata, desklet_id) {
    return new TutorEscolarDesklet(metadata, desklet_id);
}
