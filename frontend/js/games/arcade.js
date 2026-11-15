import { shuffled, ticWinner, ticMove, toggleLights, createLights, slide2048, spawn2048, canMove2048 } from './board_models.js';
import { SnakeModel, MazeModel, BreakoutModel, PongModel, mazeMap } from './arcade_models.js';

const realtime = ['maze','snake','breakout','pong'];
const symbols = ['●','▲','◆','■','✦','⬡'];

/** Exactly one board, one optional animation timer and one optional memory flip timer. */
export function createGame(type, host, report) { return new Game(type, host, report); }

class Game {
  constructor(type, host, report) {
    this.type = type; this.host = host; this.report = report; this.isRealtime = realtime.includes(type);
    this.running = false; this.done = false; this.timer = null; this.flipTimer = null; this.frame = 0; this.moves = 0;
    this.held = new Set(); this.events = new AbortController(); this.score = 0;
    host.replaceChildren();
    if (this.isRealtime) {
      this.model = type === 'maze' ? new MazeModel() : type === 'snake' ? new SnakeModel() : type === 'breakout' ? new BreakoutModel() : new PongModel();
      this.canvas = document.createElement('canvas'); this.canvas.width = 320; this.canvas.height = 320;
      this.canvas.className = 'arcade-canvas'; this.canvas.setAttribute('role','img');
      this.canvas.setAttribute('aria-label','Game board. Use the direction controls or the keyboard arrows.');
      host.appendChild(this.canvas); this.ctx = this.canvas.getContext('2d',{alpha:false});
      this._touchCanvas();
    } else {
      this.board = type === 'tic' ? Array(9).fill('') : type === 'lights' ? createLights() : type === '2048' ? spawn2048(spawn2048(Array(16).fill(0))) : shuffled([...symbols,...symbols]);
      this.matched = new Set(); this.open = [];
      if (type === '2048') {
        let start = null;
        host.addEventListener('pointerdown',event => { start = {x:event.clientX,y:event.clientY}; host.setPointerCapture(event.pointerId); }, {signal:this.events.signal});
        host.addEventListener('pointerup',event => {
          if (!start) return;
          const dx = event.clientX - start.x, dy = event.clientY - start.y; start = null;
          if (Math.max(Math.abs(dx),Math.abs(dy)) > 20) this.input(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up'));
        }, {signal:this.events.signal});
        host.addEventListener('pointercancel',() => { start = null; }, {signal:this.events.signal});
      }
    }
    this.render();
  }

  start() {
    if (!this.isRealtime || this.done || this.running) return;
    this.running = true;
    this.timer = setInterval(() => {
      this.frame++;
      if (this.type === 'snake' && this.frame % 4 === 0) this.model.step();
      if (this.type === 'maze' && this.frame % 5 === 0) this.model.step();
      if (this.type === 'breakout' || this.type === 'pong') {
        const negative = this.type === 'pong' ? 'up' : 'left', positive = this.type === 'pong' ? 'down' : 'right';
        if (this.held.has(negative)) this.model.move(-1);
        if (this.held.has(positive)) this.model.move(1);
        this.model.step();
      }
      this.done = this.model.done;
      if (this.done) this.pause();
      this.render();
    }, 34);
    this.render();
  }

  pause() {
    clearInterval(this.timer); this.timer = null; this.running = false; this.held.clear();
    if (this.flipTimer !== null) { clearTimeout(this.flipTimer); this.flipTimer = null; this.open = []; }
    this.render();
  }

  input(direction, pressed = true) {
    if (this.done) return;
    if (pressed) this.held.add(direction); else this.held.delete(direction);
    if (!pressed) return;
    if (this.type === 'snake' || this.type === 'maze') this.model.input(direction);
    if (this.type === '2048') {
      const result = slide2048(this.board,direction);
      if (result.changed) { this.board = spawn2048(result.board); this.score += result.score; this.moves++; }
      this.done = this.board.includes(2048) || !canMove2048(this.board);
      this.render();
    }
  }

  tap(direction) {
    this.input(direction,true);
    if (!this.done && (this.type === 'breakout' || this.type === 'pong')) {
      const negative = this.type === 'pong' ? 'up' : 'left', positive = this.type === 'pong' ? 'down' : 'right';
      if (direction === negative || direction === positive) this.model.move(direction === negative ? -1 : 1);
      this.render();
    }
    this.input(direction,false);
  }

  _touchCanvas() {
    let start = null;
    const point = event => {
      const rect = this.canvas.getBoundingClientRect();
      return {x:(event.clientX - rect.left) / rect.width * 320,y:(event.clientY - rect.top) / rect.height * 320};
    };
    const paddle = event => {
      const p = point(event);
      if (this.type === 'breakout') this.model.paddle = Math.max(0,Math.min(264,p.x - 28));
      if (this.type === 'pong') this.model.player = Math.max(0,Math.min(264,p.y - 28));
    };
    this.canvas.addEventListener('pointerdown',event => {
      start = point(event); this.canvas.setPointerCapture(event.pointerId); paddle(event);
    }, {signal:this.events.signal});
    this.canvas.addEventListener('pointermove',event => { if (start) paddle(event); }, {signal:this.events.signal});
    this.canvas.addEventListener('pointerup',event => {
      if (!start) return;
      const end = point(event), dx = end.x - start.x, dy = end.y - start.y;
      if (Math.max(Math.abs(dx),Math.abs(dy)) > 12) this.input(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up'));
      start = null;
    }, {signal:this.events.signal});
    this.canvas.addEventListener('pointercancel',() => { start = null; this.held.clear(); }, {signal:this.events.signal});
  }

  _cell(index) {
    if (this.done) return;
    if (this.type === 'tic' && !this.board[index]) {
      this.board[index] = 'X';
      if (!ticWinner(this.board)) this.board[ticMove(this.board)] = 'O';
      this.done = !!ticWinner(this.board); this.moves++;
    } else if (this.type === 'lights') {
      this.board = toggleLights(this.board,index); this.moves++; this.done = !this.board.some(Boolean);
    } else if (this.type === 'memory' && this.flipTimer === null && !this.matched.has(index) && !this.open.includes(index)) {
      this.open.push(index);
      if (this.open.length === 2) {
        this.moves++;
        const [a,b] = this.open;
        if (this.board[a] === this.board[b]) { this.matched.add(a); this.matched.add(b); this.open = []; this.done = this.matched.size === 12; }
        else this.flipTimer = setTimeout(() => { this.open = []; this.flipTimer = null; this.render(); },700);
      }
    }
    this.render();
  }

  _draw() {
    const c = this.ctx, m = this.model;
    c.fillStyle = '#080d16'; c.fillRect(0,0,320,320);
    if (this.type === 'snake') {
      c.strokeStyle = '#152133'; c.lineWidth = 1;
      for (let i = 0; i <= 16; i++) { c.beginPath(); c.moveTo(i * 20,0); c.lineTo(i * 20,320); c.moveTo(0,i * 20); c.lineTo(320,i * 20); c.stroke(); }
      if (m.food) { c.fillStyle = '#e1b879'; c.beginPath(); c.arc(m.food.x * 20 + 10,m.food.y * 20 + 10,6,0,Math.PI * 2); c.fill(); }
      m.body.forEach((p,i) => { c.fillStyle = i ? '#3e8b87' : '#a5e1d4'; c.fillRect(p.x * 20 + 2,p.y * 20 + 2,16,16); });
    } else if (this.type === 'maze') {
      const cell = 320 / 15;
      mazeMap.forEach((row,y) => [...row].forEach((v,x) => {
        if (v === '#') { c.fillStyle = '#263d63'; c.fillRect(x * cell + 1,y * cell + 1,cell - 2,cell - 2); }
        else if (m.pellets.has(`${x},${y}`)) { c.fillStyle = '#b8c6dc'; c.beginPath(); c.arc((x + .5) * cell,(y + .5) * cell,2,0,Math.PI * 2); c.fill(); }
      }));
      c.fillStyle = '#efd38c'; c.beginPath(); c.arc((m.player.x + .5) * cell,(m.player.y + .5) * cell,8,.25,Math.PI * 2 - .25); c.lineTo((m.player.x + .5) * cell,(m.player.y + .5) * cell); c.fill();
      c.fillStyle = '#e78eaa'; c.fillRect(m.ghost.x * cell + 4,m.ghost.y * cell + 4,14,14);
    } else if (this.type === 'breakout') {
      m.bricks.forEach((brick,i) => { if (brick.alive) { c.fillStyle = ['#b69bdc','#779acf','#6fb9bd','#dbb677'][Math.floor(i / 6)]; c.fillRect(brick.x,brick.y,45,15); } });
      c.fillStyle = '#c3d7f4'; c.fillRect(m.paddle,286,56,8);
      c.fillStyle = '#f0d3a2'; c.beginPath(); c.arc(m.ball.x,m.ball.y,5,0,Math.PI * 2); c.fill();
    } else {
      c.strokeStyle = '#263247'; c.setLineDash([5,6]); c.beginPath(); c.moveTo(160,0); c.lineTo(160,320); c.stroke(); c.setLineDash([]);
      c.fillStyle = '#8acfc2'; c.fillRect(10,m.player,8,56);
      c.fillStyle = '#bb9fdf'; c.fillRect(302,m.cpu,8,56);
      c.fillStyle = '#edf2fa'; c.beginPath(); c.arc(m.ball.x,m.ball.y,5,0,Math.PI * 2); c.fill();
    }
    if (!this.running && !this.done) {
      c.fillStyle = '#080d16bb'; c.fillRect(60,139,200,40); c.fillStyle = '#dce6f5'; c.font = '14px sans-serif'; c.textAlign = 'center'; c.fillText('Pulsa Iniciar / Continuar',160,164);
    }
  }

  _drawBoard() {
    const focused = document.activeElement?.dataset.gameCell;
    const grid = document.createElement('div'); grid.className = `arcade-grid board-${this.type}`;
    this.board.forEach((value,index) => {
      const button = document.createElement(this.type === '2048' ? 'div' : 'button');
      const visible = this.type !== 'memory' || this.matched.has(index) || this.open.includes(index);
      button.className = 'arcade-cell'; button.dataset.gameCell = index;
      if (button.tagName === 'BUTTON') button.type = 'button';
      button.textContent = this.type === 'memory' ? (visible ? value : '?') : this.type === 'lights' ? (value ? '●' : '·') : value || '';
      button.setAttribute('aria-label',`Square ${index + 1}: ${this.type === 'memory' ? (visible ? value : 'hidden') : this.type === 'lights' ? (value ? 'on' : 'off') : value || 'empty'}`);
      button.classList.toggle('cell-lit',this.type === 'lights' && value === true);
      button.classList.toggle('cell-matched',this.type === 'memory' && this.matched.has(index));
      if (this.type === '2048') button.dataset.value = value;
      else { button.disabled = this.done || (this.type === 'tic' && !!value) || (this.type === 'memory' && this.matched.has(index)); button.onclick = () => this._cell(index); }
      grid.appendChild(button);
    });
    this.host.replaceChildren(grid);
    if (focused !== undefined) this.host.querySelector(`[data-game-cell="${focused}"]:not(:disabled)`)?.focus({preventScroll:true});
  }

  render() {
    if (this.isRealtime) this._draw(); else this._drawBoard();
    let score = '', message = '';
    if (this.type === 'maze' || this.type === 'snake') score = `${this.model.score} points`;
    if (this.type === 'breakout') score = `${this.model.score} points · ${this.model.lives} lives`;
    if (this.type === 'pong') score = `You ${this.model.points[0]} : ${this.model.points[1]} CPU`;
    if (this.type === 'tic') { const winner = ticWinner(this.board); score = 'You: X · CPU: O'; message = winner === 'draw' ? 'Draw. Another match?' : winner === 'X' ? 'You won!' : winner === 'O' ? 'The CPU won. You can try again.' : 'Your turn: choose a square.'; }
    if (this.type === 'lights') { score = `${this.moves} moves`; message = this.done ? 'All lights out!' : 'Turn off every light.'; }
    if (this.type === 'memory') { score = `${this.matched.size / 2} / 6 pairs · ${this.moves} tries`; message = this.done ? 'You found all the pairs!' : 'Uncover two matching cards.'; }
    if (this.type === '2048') { score = `${this.score} points`; message = this.done ? (this.board.includes(2048) ? 'You reached 2048!' : 'No moves left. Try another match.') : 'Swipe or use the arrows to merge numbers.'; }
    if (this.isRealtime) message = this.done ? (this.type === 'maze' && this.model.won ? 'Maze completed!' : 'Match over. You can restart.') : this.running ? 'In play' : 'Match paused. Press Start / Continue.';
    this.report({score,message,done:this.done,running:this.running,realtime:this.isRealtime});
  }

  destroy() {
    clearInterval(this.timer); clearTimeout(this.flipTimer); this.timer = null; this.flipTimer = null;
    this.running = false; this.events.abort(); this.held.clear(); this.host.replaceChildren();
  }
}
