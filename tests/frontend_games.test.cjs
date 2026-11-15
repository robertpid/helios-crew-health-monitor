const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const load = async name => import(`data:text/javascript;base64,${Buffer.from(await fs.readFile(path.join(__dirname, '../frontend/js/games', name),'utf8')).toString('base64')}`);
const modules = Promise.all([load('board_models.js'),load('arcade_models.js')]);
const random = seed => () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);

test('2048 merges each tile once and preserves the sum before spawning', async () => {
  const [b] = await modules;
  const board = [2,2,2,2, 4,4,8,0, 0,0,0,0, 0,0,0,0];
  const left = b.slide2048(board,'left');
  assert.deepEqual(left.board.slice(0,8),[4,4,0,0,8,8,0,0]);
  assert.equal(left.score,16);
  for (const direction of ['left','right','up','down']) {
    assert.equal(b.slide2048(board,direction).board.reduce((a,v)=>a+v,0),board.reduce((a,v)=>a+v,0));
  }
  assert.equal(b.slide2048([2,0,0,0,...Array(12).fill(0)],'left').changed,false);
});

test('2048 detects a blocked board and never overwrites an occupied cell', async () => {
  const [b] = await modules;
  const full = [2,4,2,4,4,2,4,2,2,4,2,4,4,2,4,2];
  assert.equal(b.canMove2048(full),false);
  assert.deepEqual(b.spawn2048(full,random(1)),full);
  const partial = [...full]; partial[7] = 0;
  const next = b.spawn2048(partial,random(3));
  assert([2,4].includes(next[7]));
  next.forEach((value,index)=>{ if(index!==7) assert.equal(value,partial[index]); });
});

test('lights puzzles are solvable, including the all-cancelled random seed case', async () => {
  const [b] = await modules;
  for (let seed = 0; seed < 30; seed++) {
    let board = b.createLights(seed ? random(seed) : () => 0);
    assert(board.some(Boolean));
    const basis = Array.from({length:25},(_,i)=>b.toggleLights(Array(25).fill(false),i));
    const rows = Array.from({length:25},(_,r)=>basis.reduce((bits,column,c)=>bits | (column[r] ? 1 << c : 0), board[r] ? 1 << 25 : 0));
    const pivots=[]; let row=0;
    for(let col=0;col<25;col++) {
      const pivot=rows.findIndex((value,index)=>index>=row && (value & (1<<col)));
      if(pivot<0)continue;
      [rows[row],rows[pivot]]=[rows[pivot],rows[row]];
      for(let r=0;r<25;r++) if(r!==row && (rows[r] & (1<<col)))rows[r]^=rows[row];
      pivots.push(col);row++;
    }
    for(let r=0;r<pivots.length;r++) if(rows[r] & (1<<25))board=b.toggleLights(board,pivots[r]);
    assert.equal(board.some(Boolean),false,`seed ${seed}`);
  }
});

test('tic-tac-toe CPU wins before blocking, blocks threats and recognizes a draw', async () => {
  const [b] = await modules;
  assert.equal(b.ticMove(['O','O','','X','X','','','','']),2);
  assert.equal(b.ticMove(['X','X','','','O','','','','']),2);
  assert.equal(b.ticWinner(['X','O','X','X','O','O','O','X','X']),'draw');
  assert.equal(b.ticWinner(['X','','O','','X','O','','','X']),'X');
});

test('memory shuffle keeps exactly six pairs', async () => {
  const [b] = await modules;
  const result = b.shuffled(['A','B','C','D','E','F','A','B','C','D','E','F'],random(9));
  assert.equal(result.length,12);
  for (const letter of 'ABCDEF') assert.equal(result.filter(value=>value===letter).length,2);
});

test('snake rejects reversing, grows on food and ends at the boundary', async () => {
  const [,a] = await modules; const snake = new a.SnakeModel(random(2));
  snake.input('left'); assert.equal(snake.next,'right');
  snake.food={x:9,y:8};snake.step();assert.equal(snake.body.length,4);assert.equal(snake.score,10);
  assert(!snake.body.some(p=>p.x===snake.food.x && p.y===snake.food.y));
  snake.body=[{x:15,y:8}];snake.step();assert.equal(snake.done,true);
});

test('snake can enter the cell vacated by its tail', async () => {
  const [,a] = await modules;const snake=new a.SnakeModel(random(3));
  snake.body=[{x:1,y:1},{x:1,y:2},{x:0,y:2},{x:0,y:1}];snake.direction='up';snake.input('left');snake.food={x:10,y:10};snake.step();
  assert.equal(snake.done,false);assert.deepEqual(snake.body[0],{x:0,y:1});
});

test('maze pellets and enemy start are all reachable without crossing walls', async () => {
  const [,a] = await modules;const maze=new a.MazeModel(),seen=new Set(['1,1']),queue=[maze.player];
  for(let i=0;i<queue.length;i++) for(const [dx,dy] of Object.values(a.directions)) {
    const x=queue[i].x+dx,y=queue[i].y+dy,key=`${x},${y}`;
    if(maze.open(x,y)&&!seen.has(key)){seen.add(key);queue.push({x,y});}
  }
  for(const pellet of maze.pellets)assert(seen.has(pellet),pellet);
  assert(seen.has('13,13'));maze.input('up');maze.step();assert.deepEqual(maze.player,{x:1,y:1});
});

test('breakout paddle rebounds and loss of three balls stops the game', async () => {
  const [,a] = await modules;const game=new a.BreakoutModel();
  game.ball={x:game.paddle+28,y:280,vx:0,vy:4};game.step();assert(game.ball.vy<0);
  for(let i=0;i<3;i++){game.ball={x:160,y:324,vx:0,vy:4};game.step();}
  assert.equal(game.lives,0);assert.equal(game.done,true);
});

test('pong ends after five points and paddles stay on the board', async () => {
  const [,a] = await modules;const game=new a.PongModel();
  for(let i=0;i<5;i++){game.ball={x:319,y:160,vx:4,vy:0};game.step();}
  assert.equal(game.points[0],5);assert.equal(game.done,true);
  for(let i=0;i<100;i++)game.move(-1);assert.equal(game.player,0);
  for(let i=0;i<100;i++)game.move(1);assert.equal(game.player,264);
});
