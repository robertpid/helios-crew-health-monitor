/** Modal lifecycle and lazy loading. Game engines are absent until a game is selected. */
class GamesController {
  constructor(stateManager) {
    this._state = stateManager; this._engine = null; this._module = null; this._token = 0;
    this._catalog = [
      {id:'maze',name:'Laberinto orbital',category:'ARCADE',icon:'◕',description:'Recoge los puntos y evita al perseguidor.',instructions:'Flechas o desliza para moverte. Recoge todos los puntos sin tocar al perseguidor.'},
      {id:'snake',name:'Serpiente',category:'ARCADE',icon:'⌁',description:'Crece sin chocar contigo ni con el borde.',instructions:'Usa las flechas o desliza. Recoge la comida y evita los bordes y tu propia cola.'},
      {id:'breakout',name:'Rompebloques',category:'ARCADE',icon:'▤',description:'Una pelota, una paleta y 24 bloques.',instructions:'Mueve la paleta con izquierda/derecha o arrastra sobre el tablero. Rompe todos los bloques. Tienes 3 vidas.'},
      {id:'pong',name:'Pong',category:'ARCADE',icon:'Ⅱ',description:'Duelo clásico contra la computadora.',instructions:'Mueve tu paleta con arriba/abajo o arrastra verticalmente. Gana quien llegue a 5 puntos.'},
      {id:'tic',name:'Tres en raya',category:'LÓGICA',icon:'×○',description:'Tu X contra la O de la computadora.',instructions:'Toca una casilla vacía. Forma una línea de tres X antes que la computadora.'},
      {id:'memory',name:'Memoria',category:'MEMORIA',icon:'◇',description:'Encuentra las seis parejas de símbolos.',instructions:'Toca dos tarjetas. Recuerda los símbolos y encuentra las seis parejas con pocos intentos.'},
      {id:'2048',name:'2048',category:'LÓGICA',icon:'2048',description:'Combina números hasta alcanzar la meta.',instructions:'Usa las flechas o los botones de dirección. Los números iguales se unen. Intenta llegar a 2048.'},
      {id:'lights',name:'Luces fuera',category:'LÓGICA',icon:'⊞',description:'Apaga el tablero con movimientos en cruz.',instructions:'Toca una casilla para cambiar su luz y la de sus vecinas. El objetivo es dejar todas apagadas.'}
    ];
  }

  inicializar() {
    this._modal = document.getElementById('modalGames');
    document.getElementById('btnCloseGames').onclick = () => this.cerrar();
    document.getElementById('btnGamesBack').onclick = () => this.catalogo();
    document.getElementById('btnGamesRestart').onclick = () => this.jugar(this._selected.id);
    document.getElementById('btnGamesPause').onclick = () => {
      if (!this._engine) return;
      this._engine.running ? this._engine.pause() : this._engine.start();
    };
    this._modal.addEventListener('cancel',event => { event.preventDefault(); this.cerrar(); });
    this._modal.addEventListener('close',() => { if (!this._modal.open) this._limpiar(); });
    this._modal.addEventListener('click',event => { if (event.target === this._modal) this.cerrar(); });
    const grid = document.getElementById('gamesCatalogGrid');
    this._catalog.forEach(game => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'arcade-game-card'; button.dataset.gameId = game.id;
      const icon = document.createElement('span'); icon.className = 'arcade-card-icon'; icon.setAttribute('aria-hidden','true'); icon.textContent = game.icon;
      const category = document.createElement('small'); category.textContent = game.category;
      const title = document.createElement('strong'); title.textContent = game.name;
      const text = document.createElement('span'); text.className = 'arcade-card-description'; text.textContent = game.description;
      button.append(icon,category,title,text); button.onclick = () => this.jugar(game.id); grid.appendChild(button);
    });
    const keyDirections = {ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
    document.addEventListener('keydown',event => {
      if (this._modal.open && event.key === 'Escape') { event.preventDefault(); this.cerrar(); return; }
      if (!this._modal.open || !this._engine || event.altKey || event.ctrlKey || event.metaKey) return;
      const direction = keyDirections[event.key] || keyDirections[event.key.toLowerCase()];
      if (direction) { event.preventDefault(); this._engine.input(direction,true); }
    });
    document.addEventListener('keyup',event => { const direction = keyDirections[event.key] || keyDirections[event.key.toLowerCase()]; if (this._modal.open && this._engine && direction) this._engine.input(direction,false); });
    document.querySelectorAll('[data-game-direction]').forEach(button => {
      button.addEventListener('pointerdown',event => { event.preventDefault(); button.setPointerCapture(event.pointerId); this._engine?.input(button.dataset.gameDirection,true); });
      for (const type of ['pointerup','pointercancel','lostpointercapture']) button.addEventListener(type,() => this._engine?.input(button.dataset.gameDirection,false));
      button.addEventListener('click',event => { if (event.detail === 0) this._engine?.tap(button.dataset.gameDirection); });
    });
    document.addEventListener('visibilitychange',() => { if (document.hidden) this._engine?.pause(); });
    window.addEventListener('blur',() => this._engine?.pause());
    this._state.subscribe(state => { if (state.modalAlertaAbierto && this._modal.open) this.cerrar(); });
  }

  abrir() {
    if (this._state.getState().modalAlertaAbierto) return;
    this._returnFocus = document.activeElement;
    this.catalogo(); this._modal.showModal();
  }

  cerrar() { this._limpiar(); if (this._modal.open) this._modal.close(); this._returnFocus?.focus({preventScroll:true}); }

  _limpiar() { this._token++; this._engine?.destroy(); this._engine = null; }

  catalogo() {
    this._limpiar(); this._selected = null;
    document.getElementById('gamesCatalog').hidden = false; document.getElementById('gamesPlay').hidden = true;
    document.getElementById('gamesTitle').textContent = 'Elige tu próxima partida';
    document.getElementById('gamesLoadMessage').textContent = 'Controles táctiles y teclado. Tu partida se pausa al salir de la ventana.';
    if (this._modal.open) document.querySelector('.arcade-game-card')?.focus({preventScroll:true});
  }

  async jugar(id) {
    const game = this._catalog.find(item => item.id === id); if (!game || !this._modal.open) return;
    this._limpiar(); const token = this._token; this._selected = game;
    document.getElementById('gamesLoadMessage').textContent = 'Preparando tu partida…';
    try {
      this._module ||= import('/static/js/games/arcade.js?v=20261115_games');
      const module = await this._module;
      if (token !== this._token || !this._modal.open) return;
      document.getElementById('gamesCatalog').hidden = true; document.getElementById('gamesPlay').hidden = false;
      document.getElementById('gamesTitle').textContent = game.name;
      document.getElementById('gameInstructions').textContent = game.instructions;
      const board = document.getElementById('gameBoard');
      this._engine = module.createGame(id,board,state => this._actualizar(state));
      document.getElementById('btnGamesBack').focus({preventScroll:true});
    } catch (error) {
      this._module = null; this.catalogo();
      document.getElementById('gamesLoadMessage').textContent = 'No se pudo abrir el juego. Vuelve a seleccionarlo para intentarlo de nuevo.';
      console.error('GamesController:',error);
    }
  }

  _actualizar(state) {
    const score = document.getElementById('gameScore'), status = document.getElementById('gameStatus');
    if (score.textContent !== state.score) score.textContent = state.score;
    if (status.textContent !== state.message) status.textContent = state.message;
    const pause = document.getElementById('btnGamesPause'); pause.hidden = !state.realtime; pause.disabled = state.done;
    pause.textContent = state.running ? 'Pausar' : 'Iniciar / Continuar';
    document.getElementById('gameDpad').hidden = !state.realtime && this._selected?.id !== '2048';
  }
}

window.GamesController = GamesController;
