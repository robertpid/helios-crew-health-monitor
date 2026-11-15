/**
 * ==============================================================================
 * CAPA DE SERVICIOS: AuthService (Control de Acceso y Gestión de Tripulantes)
 * ==============================================================================
 * Gestiona la autenticación de tripulantes espaciales y cirujano de vuelo
 * mediante credenciales de usuario y clave PIN de 4 dígitos.
 */

class AuthService {
  constructor() {
    this._usuarios = [
      {
        id: "ASTRO-01",
        usuario: "astro1",
        pin: "1001",
        nombre: "Alex Mercer",
        rol: "ASTRONAUTA",
        rango: "Comandante A01",
        avatar: "👨‍🚀",
        mision: "ARES-VI (Sol 120)"
      },
      {
        id: "ASTRO-02",
        usuario: "astro2",
        pin: "2002",
        nombre: "Elena Rostova",
        rol: "ASTRONAUTA",
        rango: "Especialista A02",
        avatar: "👩‍🚀",
        mision: "ARES-VI (Sol 120)"
      },
      {
        id: "MED-01",
        usuario: "cirujano",
        pin: "9009",
        nombre: "Dr. Marcus Vance",
        rol: "CIRUJANO_VUELO",
        rango: "Cirujano de Vuelo",
        avatar: "🩺",
        mision: "Centro de Control JSC Houston"
      }
    ];

    this._claveStorage = "helios_session_user";
    this._usuarioActual = this._cargarSesionGuardada();
    this._listeners = [];
  }

  obtenerUsuarioActual() {
    return this._usuarioActual;
  }

  listarUsuariosDemo() {
    return this._usuarios.map(u => ({
      usuario: u.usuario,
      pin: u.pin,
      nombre: u.nombre,
      rol: u.rol,
      rango: u.rango,
      avatar: u.avatar
    }));
  }

  autenticar(usuario, pin) {
    const credencialUsuario = (usuario || "").trim().toLowerCase();
    const credencialPin = (pin || "").trim();

    const usuarioEncontrado = this._usuarios.find(
      u => u.usuario.toLowerCase() === credencialUsuario && u.pin === credencialPin
    );

    if (usuarioEncontrado) {
      this._usuarioActual = usuarioEncontrado;
      try {
        localStorage.setItem(this._claveStorage, JSON.stringify(usuarioEncontrado));
      } catch (e) {
        console.warn("[AuthService] No se pudo guardar la sesión en storage:", e);
      }
      this._notificarCambio();
      return { exito: true, usuario: usuarioEncontrado };
    }

    return { exito: false, error: "Credenciales inválidas. Verifique usuario o PIN." };
  }

  cerrarSesion() {
    this._usuarioActual = null;
    try {
      localStorage.removeItem(this._claveStorage);
    } catch (e) {
      console.warn("[AuthService] Error al limpiar storage:", e);
    }
    this._notificarCambio();
  }

  onCambioSesion(callback) {
    if (typeof callback === "function") {
      this._listeners.push(callback);
    }
  }

  _notificarCambio() {
    this._listeners.forEach(cb => {
      try {
        cb(this._usuarioActual);
      } catch (err) {
        console.error("[AuthService] Error en listener:", err);
      }
    });
  }

  _cargarSesionGuardada() {
    try {
      const guardado = localStorage.getItem(this._claveStorage);
      if (guardado) {
        const datos = JSON.parse(guardado);
        const existe = this._usuarios.find(u => u.usuario === datos.usuario);
        if (existe) return existe;
      }
    } catch (e) {
      console.warn("[AuthService] Error al leer sesión previa:", e);
    }
    // Usuario por defecto inicial si no hay sesión guardada: Astronauta 1
    return this._usuarios[0];
  }
}

window.authService = new AuthService();
