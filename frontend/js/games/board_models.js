/* Small, deterministic board models. No DOM, assets or timers. */
export function shuffled(values, random = Math.random) {
  const result = [...values];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

export function ticWinner(board) {
  const lines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
  for (const [a,b,c] of lines) if (board[a] && board[a] === board[b] && board[b] === board[c]) return board[a];
  return board.every(Boolean) ? 'draw' : null;
}

export function ticMove(board) {
  for (const player of ['O', 'X']) {
    for (let i = 0; i < 9; i++) if (!board[i]) {
      const candidate = [...board]; candidate[i] = player;
      if (ticWinner(candidate) === player) return i;
    }
  }
  return [4,0,2,6,8,1,3,5,7].find(index => !board[index]);
}

export function toggleLights(board, index, size = 5) {
  const result = [...board], x = index % size, y = Math.floor(index / size);
  for (const [dx,dy] of [[0,0],[0,1],[0,-1],[1,0],[-1,0]]) {
    const nx = x + dx, ny = y + dy;
    if (nx >= 0 && nx < size && ny >= 0 && ny < size) result[ny * size + nx] = !result[ny * size + nx];
  }
  return result;
}

export function createLights(random = Math.random) {
  let board = Array(25).fill(false);
  for (let i = 0; i < 20; i++) board = toggleLights(board, Math.floor(random() * 25));
  return board.some(Boolean) ? board : toggleLights(board, 12);
}

export function slide2048(board, direction) {
  const result = Array(16).fill(0); let score = 0;
  for (let line = 0; line < 4; line++) {
    const indexes = Array.from({length:4}, (_, step) => {
      if (direction === 'left') return line * 4 + step;
      if (direction === 'right') return line * 4 + 3 - step;
      if (direction === 'up') return step * 4 + line;
      return (3 - step) * 4 + line;
    });
    const values = indexes.map(index => board[index]).filter(Boolean), merged = [];
    for (let i = 0; i < values.length; i++) {
      if (values[i] === values[i + 1]) { merged.push(values[i] * 2); score += values[i] * 2; i++; }
      else merged.push(values[i]);
    }
    indexes.forEach((index, i) => { result[index] = merged[i] || 0; });
  }
  return { board: result, score, changed: result.some((value, index) => value !== board[index]) };
}

export function spawn2048(board, random = Math.random) {
  const empty = board.map((value,index) => value ? -1 : index).filter(index => index >= 0), result = [...board];
  if (empty.length) result[empty[Math.floor(random() * empty.length)]] = random() < .9 ? 2 : 4;
  return result;
}

export function canMove2048(board) {
  return board.some(value => value === 0) || ['left','right','up','down'].some(direction => slide2048(board, direction).changed);
}
