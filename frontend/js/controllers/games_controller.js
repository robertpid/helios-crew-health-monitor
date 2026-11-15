/** Modal lifecycle and lazy loading. Game engines are absent until a game is selected. */
class GamesController {
  constructor(stateManager) {
    this._state = stateManager; this._engine = null; this._module = null; this._token = 0;
    this._catalog = [
      {id:'maze',name:'Orbital maze',category:'ARCADE',icon:'◕',description:'Collect the dots and avoid the chaser.',instructions:'Arrows or swipe to move. Collect every dot without touching the chaser.'},
      {id:'snake',name:'Snake',category:'ARCADE',icon:'⌁',description:'Grow without hitting yourself or the edge.',instructions:'Use the arrows or swipe. Collect the food and avoid the edges and your own tail.'},
      {id:'breakout',name:'Breakout',category:'ARCADE',icon:'▤',description:'One ball, one paddle and 24 bricks.',instructions:'Move the paddle with left/right or drag across the board. Break every brick. You have 3 lives.'},
      {id:'pong',name:'Pong',category:'ARCADE',icon:'Ⅱ',description:'Classic duel against the computer.',instructions:'Move your paddle with up/down or drag vertically. First to 5 points wins.'},
      {id:'tic',name:'Tic-tac-toe',category:'LOGIC',icon:'×○',description:'Your X against the computer’s O.',instructions:'Tap an empty square. Make a line of three X before the computer does.'},
      {id:'memory',name:'Memory',category:'MEMORY',icon:'◇',description:'Find the six pairs of symbols.',instructions:'Tap two cards. Remember the symbols and find all six pairs in as few tries as possible.'},
      {id:'2048',name:'2048',category:'LOGIC',icon:'2048',description:'Merge numbers until you reach the goal.',instructions:'Use the arrows or the direction buttons. Equal numbers merge. Try to reach 2048.'},
      {id:'lights',name:'Lights out',category:'LOGIC',icon:'⊞',description:'Turn off the board with cross-shaped moves.',instructions:'Tap a square to toggle its light and its neighbors’. The goal is to leave them all off.'}
    ];
  }

  initialize() {
    this._modal = document.getElementById('modalGames');
    document.getElementById('btnCloseGames').onclick = () => this.close();
    document.getElementById('btnGamesBack').onclick = () => this.catalog();
    document.getElementById('btnGamesRestart').onclick = () => this.play(this._selected.id);
    document.getElementById('btnGamesPause').onclick = () => {
      if (!this._engine) return;
      this._engine.running ? this._engine.pause() : this._engine.start();
    };
    this._modal.addEventListener('cancel',event => { event.preventDefault(); this.close(); });
    this._modal.addEventListener('close',() => { if (!this._modal.open) this._clear(); });
    this._modal.addEventListener('click',event => { if (event.target === this._modal) this.close(); });
    const grid = document.getElementById('gamesCatalogGrid');
    this._catalog.forEach(game => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'arcade-game-card'; button.dataset.gameId = game.id;
      const icon = document.createElement('span'); icon.className = 'arcade-card-icon'; icon.setAttribute('aria-hidden','true'); icon.textContent = game.icon;
      const category = document.createElement('small'); category.textContent = game.category;
      const title = document.createElement('strong'); title.textContent = game.name;
      const text = document.createElement('span'); text.className = 'arcade-card-description'; text.textContent = game.description;
      button.append(icon,category,title,text); button.onclick = () => this.play(game.id); grid.appendChild(button);
    });
    const keyDirections = {ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
    document.addEventListener('keydown',event => {
      if (this._modal.open && event.key === 'Escape') { event.preventDefault(); this.close(); return; }
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
    this._state.subscribe(state => { if (state.alertModalOpen && this._modal.open) this.close(); });
  }

  open() {
    if (this._state.getState().alertModalOpen) return;
    this._returnFocus = document.activeElement;
    this.catalog(); this._modal.showModal();
  }

  close() { this._clear(); if (this._modal.open) this._modal.close(); this._returnFocus?.focus({preventScroll:true}); }

  _clear() { this._token++; this._engine?.destroy(); this._engine = null; }

  catalog() {
    this._clear(); this._selected = null;
    document.getElementById('gamesCatalog').hidden = false; document.getElementById('gamesPlay').hidden = true;
    document.getElementById('gamesTitle').textContent = 'Choose your next match';
    document.getElementById('gamesLoadMessage').textContent = 'Touch and keyboard controls. Your match pauses when you leave the window.';
    if (this._modal.open) document.querySelector('.arcade-game-card')?.focus({preventScroll:true});
  }

  async play(id) {
    const game = this._catalog.find(item => item.id === id); if (!game || !this._modal.open) return;
    this._clear(); const token = this._token; this._selected = game;
    document.getElementById('gamesLoadMessage').textContent = 'Preparing your match…';
    try {
      this._module ||= import('/static/js/games/arcade.js?v=20261115_games');
      const module = await this._module;
      if (token !== this._token || !this._modal.open) return;
      document.getElementById('gamesCatalog').hidden = true; document.getElementById('gamesPlay').hidden = false;
      document.getElementById('gamesTitle').textContent = game.name;
      document.getElementById('gameInstructions').textContent = game.instructions;
      const board = document.getElementById('gameBoard');
      this._engine = module.createGame(id,board,state => this._update(state));
      document.getElementById('btnGamesBack').focus({preventScroll:true});
    } catch (error) {
      this._module = null; this.catalog();
      document.getElementById('gamesLoadMessage').textContent = 'The game could not be opened. Select it again to retry.';
      console.error('GamesController:',error);
    }
  }

  _update(state) {
    const score = document.getElementById('gameScore'), status = document.getElementById('gameStatus');
    if (score.textContent !== state.score) score.textContent = state.score;
    if (status.textContent !== state.message) status.textContent = state.message;
    const pause = document.getElementById('btnGamesPause'); pause.hidden = !state.realtime; pause.disabled = state.done;
    pause.textContent = state.running ? 'Pause' : 'Start / Continue';
    document.getElementById('gameDpad').hidden = !state.realtime && this._selected?.id !== '2048';
  }
}

window.GamesController = GamesController;
