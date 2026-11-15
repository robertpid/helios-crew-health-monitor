/**
 * CAPA DE SERVICIOS: OftalmicoService
 * Motor de Evaluación Oftalmológica Preliminar y Protocolo SANS (NASA JSC).
 * Batería de 5 etapas: Agudeza (Tumbling E), Astigmatismo (Dial),
 * Contraste (Landolt C), Visión de Cerca y Visión Cromática (Ishihara).
 * Generación aleatoria anti-memorización y atajos de teclado (Clean Code & SRP).
 * Rigurosamente bajo 400 líneas.
 */

class OftalmicoService {
  constructor(soundService = null) {
    this._sound = soundService || window.soundService;
    this._modalAbierto = false;

    // Catálogo base de láminas de Ishihara para Visión Cromática
    this._catalogoCromatica = [
      { img: "/static/assets/oftalmico/ishihara_1.webp", ans: "12", opts: ["12", "15", "17", "nothing"] },
      { img: "/static/assets/oftalmico/ishihara_2.webp", ans: "29", opts: ["28", "29", "79", "nothing"] },
      { img: "/static/assets/oftalmico/ishihara_3.webp", ans: "15", opts: ["15", "16", "45", "nothing"] },
      { img: "/static/assets/oftalmico/ishihara_4.webp", ans: "97", opts: ["82", "91", "97", "nothing"] },
      { img: "/static/assets/oftalmico/ishihara_5.webp", ans: "16", opts: ["10", "16", "48", "nothing"] },
      { img: "/static/assets/oftalmico/ishihara_6.webp", ans: "nothing", opts: ["11", "20", "88", "nothing"] },
      { img: "/static/assets/oftalmico/ishihara_7.webp", ans: "6", opts: ["5", "6", "8", "nothing"] }
    ];

    window.addEventListener("keydown", (e) => this._manejarTeclado(e));
    this._resetEstado();
  }

  _barajarArray(array) {
    const copia = [...array];
    for (let i = copia.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copia[i], copia[j]] = [copia[j], copia[i]];
    }
    return copia;
  }

  _generarPruebasAleatorias() {
    const DIRS = [
      { dir: "up", rot: 270 },
      { dir: "down", rot: 90 },
      { dir: "left", rot: 180 },
      { dir: "right", rot: 0 }
    ];

    // 1. Agudeza: 10 tamaños con orientación 100% aleatoria para evitar sesgo de memorización
    const tamanos = [68, 60, 52, 44, 38, 32, 28, 24, 20, 16];
    this._laminasAgudeza = tamanos.map(sz => {
      const p = DIRS[Math.floor(Math.random() * DIRS.length)];
      return { dir: p.dir, rot: p.rot, sz };
    });

    // 2. Contraste: 8 niveles con orientación de abertura 100% aleatoria
    const opacidades = [1.0, 0.8, 0.65, 0.5, 0.38, 0.28, 0.20, 0.12];
    this._laminasContraste = opacidades.map(op => {
      const p = DIRS[Math.floor(Math.random() * DIRS.length)];
      return { dir: p.dir, rot: p.rot, op };
    });

    // 3. Ishihara: orden aleatorio de láminas y de sus botones de opciones
    this._laminasCromatica = this._barajarArray(this._catalogoCromatica).map(item => ({
      ...item,
      opts: this._barajarArray(item.opts)
    }));
  }

  _manejarTeclado(e) {
    if (!this._modalAbierto) return;
    const mapa = {
      ArrowUp: "up",
      ArrowDown: "down",
      ArrowLeft: "left",
      ArrowRight: "right"
    };
    const dir = mapa[e.key];
    if (!dir) return;

    if (this._etapa === 1) {
      e.preventDefault();
      this.responderAgudeza(dir);
    } else if (this._etapa === 3) {
      e.preventDefault();
      this.responderContraste(dir);
    }
  }

  _resetEstado() {
    this._etapa = 0;
    this._subIndice = 0;
    this._aciertosAgudeza = 0;
    this._astigmatismoOD = false;
    this._astigmatismoOI = false;
    this._aciertosContraste = 0;
    this._resultadoCerca = "completa";
    this._aciertosCromatica = 0;
    this._generarPruebasAleatorias();
  }

  abrirModal() {
    this._sound?.reproducirClick?.();
    this._modalAbierto = true;
    this._resetEstado();
    const modal = document.getElementById("modalOftalmico");
    if (modal) modal.style.display = "flex";
    this._mostrarVista("oftalPasoIntro");
    this._actualizarProgreso("INSPECCIÓN", 0);
  }

  cerrarModal() {
    this._sound?.reproducirClick?.();
    this._modalAbierto = false;
    const modal = document.getElementById("modalOftalmico");
    if (modal) modal.style.display = "none";
  }

  iniciarEtapa1() {
    this._sound?.reproducirClick?.();
    this._etapa = 1;
    this._subIndice = 0;
    this._aciertosAgudeza = 0;
    this._mostrarVista("oftalPasoAgudeza");
    this._renderizarOptotipoE();
    this._actualizarProgreso("ETAPA 1/5", 15);
  }

  _renderizarOptotipoE() {
    const item = this._laminasAgudeza[this._subIndice];
    const el = document.getElementById("oftalOptotipoE");
    const tag = document.getElementById("oftalAgudezaIndice");
    const ojoTag = document.getElementById("oftalAgudezaOjoTag");
    if (tag) tag.innerText = this._subIndice + 1;
    if (ojoTag) {
      ojoTag.innerText = this._subIndice < 5 
        ? "OJO DERECHO (Tápate el ojo izquierdo)" 
        : "OJO IZQUIERDO (Tápate el ojo derecho)";
    }
    if (el && item) {
      el.style.transform = `rotate(${item.rot}deg)`;
      el.style.fontSize = `${item.sz}px`;
    }
  }

  responderAgudeza(direccion) {
    this._sound?.reproducirClick?.();
    const item = this._laminasAgudeza[this._subIndice];
    if (item && item.dir === direccion) this._aciertosAgudeza++;

    this._subIndice++;
    if (this._subIndice < this._laminasAgudeza.length) {
      this._renderizarOptotipoE();
    } else {
      this._iniciarEtapa2();
    }
  }

  _iniciarEtapa2() {
    this._etapa = 2;
    this._subIndice = 0; // 0: OD, 1: OI
    this._mostrarVista("oftalPasoAstigmatismo");
    this._actualizarProgreso("ETAPA 2/5", 35);
    const ojoTag = document.getElementById("oftalAstigOjoTag");
    if (ojoTag) ojoTag.innerText = "OJO DERECHO (Tápate el ojo izquierdo)";
  }

  responderAstigmatismo(veLineaOscura) {
    this._sound?.reproducirClick?.();
    if (this._subIndice === 0) {
      this._astigmatismoOD = veLineaOscura;
      this._subIndice = 1;
      const ojoTag = document.getElementById("oftalAstigOjoTag");
      if (ojoTag) ojoTag.innerText = "OJO IZQUIERDO (Tápate el ojo derecho)";
    } else {
      this._astigmatismoOI = veLineaOscura;
      this._iniciarEtapa3();
    }
  }

  _iniciarEtapa3() {
    this._etapa = 3;
    this._subIndice = 0;
    this._aciertosContraste = 0;
    this._mostrarVista("oftalPasoContraste");
    this._renderizarLandoltC();
    this._actualizarProgreso("ETAPA 3/5", 55);
  }

  _renderizarLandoltC() {
    const item = this._laminasContraste[this._subIndice];
    const el = document.getElementById("oftalSvgLandolt");
    const tag = document.getElementById("oftalContrasteIndice");
    if (tag) tag.innerText = this._subIndice + 1;
    if (el && item) {
      el.style.transform = `rotate(${item.rot}deg)`;
      el.style.opacity = item.op;
    }
  }

  responderContraste(direccion) {
    this._sound?.reproducirClick?.();
    const item = this._laminasContraste[this._subIndice];
    if (item && item.dir === direccion) this._aciertosContraste++;

    this._subIndice++;
    if (this._subIndice < this._laminasContraste.length) {
      this._renderizarLandoltC();
    } else {
      this._iniciarEtapa4();
    }
  }

  _iniciarEtapa4() {
    this._etapa = 4;
    this._mostrarVista("oftalPasoCerca");
    this._actualizarProgreso("ETAPA 4/5", 75);
  }

  responderCerca(resultado) {
    this._sound?.reproducirClick?.();
    this._resultadoCerca = resultado;
    this._iniciarEtapa5();
  }

  _iniciarEtapa5() {
    this._etapa = 5;
    this._subIndice = 0;
    this._aciertosCromatica = 0;
    this._mostrarVista("oftalPasoCromatica");
    this._renderizarIshihara();
    this._actualizarProgreso("ETAPA 5/5", 90);
  }

  _renderizarIshihara() {
    const item = this._laminasCromatica[this._subIndice];
    const imgEl = document.getElementById("oftalImgIshihara");
    const idxEl = document.getElementById("oftalCromaticaIndice");
    const contOpts = document.getElementById("oftalOpcionesIshihara");
    if (idxEl) idxEl.innerText = this._subIndice + 1;
    if (imgEl && item) imgEl.src = item.img;

    if (contOpts && item) {
      contOpts.innerHTML = item.opts.map(opt => `
        <button class="btn-hud" onclick="window.oftalmicoService?.responderCromatica('${opt}')" style="padding:10px 14px; font-size:13px; font-weight:600;">
          ${opt === "nothing" ? "Ninguno / Nada" : opt}
        </button>
      `).join("");
    }
  }

  responderCromatica(seleccion) {
    this._sound?.reproducirClick?.();
    const item = this._laminasCromatica[this._subIndice];
    if (item && item.ans === seleccion) this._aciertosCromatica++;

    this._subIndice++;
    if (this._subIndice < this._laminasCromatica.length) {
      this._renderizarIshihara();
    } else {
      this._mostrarResultados();
    }
  }

  _mostrarResultados() {
    this._etapa = 6;
    this._mostrarVista("oftalPasoResultados");
    this._actualizarProgreso("COMPLETADO", 100);

    const setBadge = (idVal, idBadge, valTxt, estado) => {
      const elVal = document.getElementById(idVal), elB = document.getElementById(idBadge);
      if (elVal) elVal.innerText = valTxt;
      if (elB) {
        elB.innerText = estado;
        if (estado === "Estable") {
          elB.style.background = "rgba(0, 255, 136, 0.15)";
          elB.style.color = "var(--neon-green)";
        } else if (estado === "Precaución") {
          elB.style.background = "rgba(245, 158, 11, 0.15)";
          elB.style.color = "#f59e0b";
        } else {
          elB.style.background = "rgba(255, 34, 85, 0.15)";
          elB.style.color = "var(--neon-red)";
        }
      }
    };

    // 1. Agudeza visual (8-10 Estable, 6-7 Precaución, 0-5 Revisión)
    const estAgudeza = this._aciertosAgudeza >= 8 ? "Estable" : (this._aciertosAgudeza >= 6 ? "Precaución" : "Revisión");
    setBadge("resAgudezaVal", "resAgudezaBadge", `${this._aciertosAgudeza}/10`, estAgudeza);

    // 2. Astigmatismo (Ambos no = Estable, 1 sí = Precaución, Ambos sí = Revisar)
    let estAstig = "Estable";
    if (this._astigmatismoOD && this._astigmatismoOI) estAstig = "Revisión";
    else if (this._astigmatismoOD || this._astigmatismoOI) estAstig = "Precaución";
    const txtAstig = `${this._astigmatismoOD ? "OD(+)" : "OD(-)"} / ${this._astigmatismoOI ? "OI(+)" : "OI(-)"}`;
    setBadge("resAstigVal", "resAstigBadge", txtAstig, estAstig);

    // 3. Contraste visual (7-8 Estable, 5-6 Precaución, 0-4 Revisión)
    const estContraste = this._aciertosContraste >= 7 ? "Estable" : (this._aciertosContraste >= 5 ? "Precaución" : "Revisión");
    setBadge("resContrasteVal", "resContrasteBadge", `${this._aciertosContraste}/8`, estContraste);

    // 4. Visión de cerca (completa=Estable, parcial=Precaución, dificil=Revisión)
    const estCerca = this._resultadoCerca === "completa" ? "Estable" : (this._resultadoCerca === "parcial" ? "Precaución" : "Revisión");
    const txtCerca = this._resultadoCerca === "completa" ? "Completa" : (this._resultadoCerca === "parcial" ? "Parcial" : "Reducida");
    setBadge("resCercaVal", "resCercaBadge", txtCerca, estCerca);

    // 5. Visión cromática (6-7 Estable, 4-5 Precaución, 0-3 Revisión)
    const estCromatica = this._aciertosCromatica >= 6 ? "Estable" : (this._aciertosCromatica >= 4 ? "Precaución" : "Revisión");
    setBadge("resCromaticaVal", "resCromaticaBadge", `${this._aciertosCromatica}/7`, estCromatica);
  }

  guardarYTransmitir() {
    this._sound?.reproducirClick?.();
    window.wellnessController?.sumarExp?.(50);
    this.cerrarModal();

    const msg = `📡 <strong>EVALUACIÓN OFTALMOLÓGICA SANS:</strong> Batería Sol 120 completada. Agudeza: ${this._aciertosAgudeza}/10 · Contraste: ${this._aciertosContraste}/8. Datos transmitidos a Houston Flight Surgeon.`;
    window.wellnessController?._mostrarFeedback?.(msg);
  }

  _mostrarVista(idVista) {
    const vistas = [
      "oftalPasoIntro", "oftalPasoAgudeza", "oftalPasoAstigmatismo",
      "oftalPasoContraste", "oftalPasoCerca", "oftalPasoCromatica", "oftalPasoResultados"
    ];
    vistas.forEach(v => {
      const el = document.getElementById(v);
      if (el) el.style.display = (v === idVista) ? "block" : "none";
    });
  }

  _actualizarProgreso(etiqueta, pct) {
    const tag = document.getElementById("oftalProgresoTag");
    const bar = document.getElementById("oftalProgressBar");
    if (tag) tag.innerText = etiqueta;
    if (bar) bar.style.width = `${pct}%`;
  }
}

window.oftalmicoService = new OftalmicoService(window.soundService);
