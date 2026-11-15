export const directions = { up: [0,-1], down: [0,1], left: [-1,0], right: [1,0] };
export class SnakeModel {
  constructor(random = Math.random) {
    this.random = random; this.body = [{x:8,y:8},{x:7,y:8},{x:6,y:8}];
    this.direction = 'right'; this.next = 'right'; this.done = false; this.score = 0; this.food = this._food();
  }
  _food() {
    const empty = [];
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) if (!this.body.some(p => p.x === x && p.y === y)) empty.push({x,y});
    return empty[Math.floor(this.random() * empty.length)] || null;
  }
  input(direction) {
    if (!directions[direction]) return;
    const a = directions[this.direction], b = directions[direction];
    if (a[0] !== -b[0] || a[1] !== -b[1]) this.next = direction;
  }
  step() {
    if (this.done) return;
    this.direction = this.next;
    const [dx,dy] = directions[this.direction], head = {x:this.body[0].x + dx, y:this.body[0].y + dy};
    const eat = this.food && head.x === this.food.x && head.y === this.food.y;
    const occupied = eat ? this.body : this.body.slice(0,-1);
    if (head.x < 0 || head.x >= 16 || head.y < 0 || head.y >= 16 || occupied.some(p => p.x === head.x && p.y === head.y)) { this.done = true; return; }
    this.body.unshift(head);
    if (eat) { this.score += 10; this.food = this._food(); if (!this.food) this.done = true; }
    else this.body.pop();
  }
}

export const mazeMap = [
  '###############', '#.....#.......#', '#.###.#.###.#.#', '#...#...#...#.#',
  '###.###.#.###.#', '#...#...#.....#', '#.#.#.#####.#.#', '#.#.........#.#',
  '#.#####.###.#.#', '#.....#...#...#', '#.###.###.###.#', '#.#.....#.....#',
  '#.#.###.#.###.#', '#.....#.......#', '###############'
];

export class MazeModel {
  constructor() {
    this.player = {x:1,y:1}; this.ghost = {x:13,y:13}; this.direction = null; this.tick = 0;
    this.pellets = new Set(); this.score = 0; this.done = false; this.won = false;
    mazeMap.forEach((row,y) => [...row].forEach((cell,x) => { if (cell !== '#') this.pellets.add(`${x},${y}`); }));
    this.pellets.delete('1,1');
  }
  open(x,y) { return mazeMap[y]?.[x] === '.'; }
  input(direction) { if (directions[direction]) this.direction = direction; }
  _ghostStep() {
    const queue = [{...this.ghost,first:null}], seen = new Set([`${this.ghost.x},${this.ghost.y}`]);
    for (let i = 0; i < queue.length; i++) {
      const node = queue[i];
      if (node.x === this.player.x && node.y === this.player.y) { if (node.first) this.ghost = node.first; return; }
      for (const [dx,dy] of Object.values(directions)) {
        const x = node.x + dx, y = node.y + dy, key = `${x},${y}`;
        if (this.open(x,y) && !seen.has(key)) { seen.add(key); queue.push({x,y,first:node.first || {x,y}}); }
      }
    }
  }
  step() {
    if (this.done || !this.direction) return;
    const [dx,dy] = directions[this.direction], x = this.player.x + dx, y = this.player.y + dy;
    const previous = {...this.player};
    if (this.open(x,y)) this.player = {x,y};
    if (this.pellets.delete(`${this.player.x},${this.player.y}`)) this.score += 10;
    const ghostBefore = {...this.ghost};
    if (++this.tick % 3 === 0) this._ghostStep();
    const same = (a,b) => a.x === b.x && a.y === b.y;
    if (same(this.player,ghostBefore) || same(this.player,this.ghost) || (same(previous,this.ghost) && same(this.player,ghostBefore))) this.done = true;
    if (!this.pellets.size) { this.done = true; this.won = true; }
  }
}

export class BreakoutModel {
  constructor() {
    this.paddle = 132; this.ball = {x:160,y:240,vx:3,vy:-4}; this.score = 0; this.lives = 3; this.done = false;
    this.bricks = Array.from({length:24},(_,i) => ({x:12 + i % 6 * 50,y:28 + Math.floor(i / 6) * 21,alive:true}));
  }
  move(direction) { this.paddle = Math.max(0,Math.min(264,this.paddle + direction * 12)); }
  step() {
    if (this.done) return;
    const b = this.ball, oldY = b.y;
    b.x += b.vx; b.y += b.vy;
    if (b.x < 5 || b.x > 315) { b.x = Math.max(5,Math.min(315,b.x)); b.vx *= -1; }
    if (b.y < 5) { b.y = 5; b.vy = Math.abs(b.vy); }
    for (const brick of this.bricks) if (brick.alive && b.x + 5 >= brick.x && b.x - 5 <= brick.x + 45 && b.y + 5 >= brick.y && b.y - 5 <= brick.y + 15) {
      brick.alive = false; this.score += 10; b.vy *= -1; break;
    }
    if (b.vy > 0 && oldY <= 281 && b.y >= 281 && b.x >= this.paddle - 5 && b.x <= this.paddle + 61) {
      b.y = 281; b.vy = -Math.abs(b.vy); b.vx = (b.x - this.paddle - 28) / 10;
    }
    if (b.y > 325) { this.lives--; if (!this.lives) this.done = true; else this.ball = {x:this.paddle + 28,y:240,vx:3,vy:-4}; }
    if (this.bricks.every(brick => !brick.alive)) this.done = true;
  }
}

export class PongModel {
  constructor() {
    this.player = 132; this.cpu = 132; this.points = [0,0]; this.done = false; this.serve(1);
  }
  serve(direction) { this.ball = {x:160,y:160,vx:4 * direction,vy:2.5}; }
  move(direction) { this.player = Math.max(0,Math.min(264,this.player + direction * 12)); }
  step() {
    if (this.done) return;
    const b = this.ball; b.x += b.vx; b.y += b.vy;
    this.cpu = Math.max(0,Math.min(264,this.cpu + Math.max(-2.5,Math.min(2.5,b.y - this.cpu - 28))));
    if (b.y < 5 || b.y > 315) { b.y = Math.max(5,Math.min(315,b.y)); b.vy *= -1; }
    if (b.vx < 0 && b.x <= 20 && b.x >= 12 && b.y >= this.player && b.y <= this.player + 56) { b.x = 20; b.vx = Math.abs(b.vx); b.vy = (b.y - this.player - 28) / 9; }
    if (b.vx > 0 && b.x >= 300 && b.x <= 308 && b.y >= this.cpu && b.y <= this.cpu + 56) { b.x = 300; b.vx = -Math.abs(b.vx); }
    if (b.x < 0 || b.x > 320) { this.points[b.x > 320 ? 0 : 1]++; this.serve(b.x > 320 ? -1 : 1); }
    this.done = this.points.some(score => score >= 5);
  }
}
