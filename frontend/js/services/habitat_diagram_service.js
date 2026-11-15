/** Reference callouts over the user's raster cutouts; no animation loop or canvas. */
class HabitatDiagramService {
  constructor() {
    this._model = 'orion';
    this._parts = [
      {key:'co2',label:'CO₂',name:'Life support and CO₂',color:'var(--c-green)',side:'left',y:55},
      {key:'rad',label:'RAD',name:'Shielding and radiation',color:'var(--c-amber)',side:'left',y:205},
      {key:'temp',label:'TEMP',name:'Thermal control',color:'var(--c-cyan)',side:'left',y:380},
      {key:'press',label:'PRES',name:'Hull and pressure',color:'var(--c-cyan)',side:'right',y:115},
      {key:'hum',label:'HUM',name:'Cabin and humidity',color:'var(--c-blue)',side:'right',y:325}
    ];
    this._geometry = {
      orion: {width:1993,height:1525,points:{co2:[.31,.48],rad:[.53,.38],temp:[.73,.44],press:[.41,.22],hum:[.27,.65]}},
      mars: {width:2024,height:1296,points:{co2:[.25,.40],rad:[.46,.84],temp:[.65,.35],press:[.53,.50],hum:[.28,.63]}},
      iss: {width:2212,height:1416,points:{co2:[.60,.60],rad:[.43,.50],temp:[.45,.35],press:[.72,.68],hum:[.68,.62]}}
    };
  }

  initialize() {
    this._svg = document.getElementById('habitatConnectors');
    this._markers = document.getElementById('habitatMarkers');
    if (!this._svg || !this._markers) return;
    this._parts.forEach(part => {
      const group = document.createElementNS('http://www.w3.org/2000/svg','g');
      group.classList.add('habitat-connector-line'); group.dataset.habitatLine = part.key;
      group.style.setProperty('--sensor-color',part.color);
      const line = document.createElementNS(group.namespaceURI,'polyline');
      const dot = document.createElementNS(group.namespaceURI,'circle');
      line.setAttribute('fill','none'); dot.setAttribute('r','4');
      group.append(line,dot); this._svg.appendChild(group);
      for (const kind of ['point','label']) {
        const button = document.createElement('button'); button.type = 'button';
        button.className = `habitat-module-node habitat-${kind}`; button.dataset.habitatModule = part.key;
        button.dataset.markerKind = kind; button.dataset.side = part.side;
        button.setAttribute('aria-label',`${part.name}: view indicator`); button.setAttribute('aria-pressed','false');
        button.style.setProperty('--sensor-color',part.color);
        button.textContent = kind === 'label' ? part.label : '';
        button.addEventListener('mouseenter',() => { if (matchMedia('(hover: hover)').matches) window.hudController?.focusHabitatModule(part.key); });
        button.addEventListener('mouseleave',() => { if (matchMedia('(hover: hover)').matches) window.hudController?.unfocusHabitatModule(); });
        button.onclick = () => {
          if (window.innerWidth < 900) {
            window.hudController?.changeHabitatDetail('sensors');
            document.querySelector(`.habitat-readouts [data-habitat-card="${part.key}"]`)?.focus({preventScroll:true});
          }
          window.hudController?.focusHabitatModule(part.key);
        };
        this._markers.appendChild(button);
      }
    });
    this.update(this._model);
    window.addEventListener('resize',() => this.update(this._model));
  }

  update(model) {
    if (!this._geometry[model] || !this._svg) return;
    this._model = model;
    const compact = window.innerWidth < 900, geometry = this._geometry[model];
    const box = compact ? {x:148,y:60,w:384,h:380} : {x:184,y:90,w:312,h:320};
    const scale = Math.min(box.w / geometry.width, box.h / geometry.height);
    const width = geometry.width * scale, height = geometry.height * scale;
    const left = box.x + (box.w - width) / 2, top = box.y + (box.h - height) / 2;
    const image = document.getElementById('habitatImage');
    image.width = geometry.width; image.height = geometry.height;
    this._parts.forEach(part => {
      const p = geometry.points[part.key], x = left + p[0] * width, y = top + p[1] * height;
      const end = part.side === 'left' ? (compact ? 118 : 198) : (compact ? 562 : 482);
      const elbow = part.side === 'left' ? (compact ? 168 : 238) : (compact ? 512 : 442);
      const group = this._svg.querySelector(`[data-habitat-line="${part.key}"]`);
      group.querySelector('polyline').setAttribute('points',`${x.toFixed(1)},${y.toFixed(1)} ${elbow},${part.y} ${end},${part.y}`);
      group.querySelector('circle').setAttribute('cx',x.toFixed(1)); group.querySelector('circle').setAttribute('cy',y.toFixed(1));
      for (const marker of this._markers.querySelectorAll(`[data-habitat-module="${part.key}"]`)) {
        marker.style.top = `${(marker.dataset.markerKind === 'point' ? y : part.y) / 5}%`;
        if (marker.dataset.markerKind === 'point') marker.style.left = `${x / 6.8}%`;
      }
    });
  }
}

window.HabitatDiagramService = HabitatDiagramService;
