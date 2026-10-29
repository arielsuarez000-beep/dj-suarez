// Pruebas aisladas: no modifican el audio ni el motor de mezcla.
// Ejecutar desde la raíz del repositorio: node tests/seleccion.test.cjs
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('index.html', 'utf8');
function sourceOf(name) {
  const start = html.indexOf('function ' + name + '(');
  assert(start >= 0, 'Falta la función ' + name);
  const brace = html.indexOf('{', start);
  let depth = 0;
  for (let i = brace; i < html.length; i++) {
    if (html[i] === '{') depth++;
    if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('Función incompleta: ' + name);
}
const controls = {
  noRepeat: {value: '10'}, shuffle: {checked: false},
  bpmMatch: {checked: true}, djSelectionMode: {value: 'fiesta'}
};
const sandbox = {
  tracks: [], sessionPlayed: [], current: 0,
  scopedIndices() { return sandbox.tracks.map((t,i) => ({t,i})); },
  $(id) { return controls[id] || null; },
  requestedNextTrack: null, Math, Set, Number
};
vm.createContext(sandbox);
for (const name of ['artistName','bpmDistance','rankNextIndex','djAutoEligible','proSimilarNext']) {
  vm.runInContext(sourceOf(name), sandbox);
}
let pass = 0, fail = 0;
function test(name, run) {
  try { run(); console.log('OK  ' + name); pass++; }
  catch(e) { console.error('FAIL ' + name + ': ' + e.message); fail++; }
}
function reset(n=20) {
  sandbox.tracks = Array.from({length:n},(_,i)=>({
    name: 'Artista ' + i + ' - Canción ' + i + '.mp3',
    bpm: 100 + (i%4), genre: 'cumbia', energy: 0.65,
    beatConfidence: 0.8
  }));
  sandbox.current = 0;
  sandbox.sessionPlayed = [sandbox.tracks[0]];
}
test('Sin repetir hasta completar una lista de 20', () => {
  reset();
  const heard = sandbox.sessionPlayed.slice();
  let from = 0;
  for(let n=1;n<20;n++) {
    const i = sandbox.rankNextIndex(from,heard,new Set());
    assert(i >= 0 && !heard.includes(sandbox.tracks[i]));
    heard.push(sandbox.tracks[i]); from=i;
  }
  assert.equal(new Set(heard).size,20);
});
test('Nueva vuelta después de escuchar toda la lista', () => {
  reset(5);
  sandbox.sessionPlayed = sandbox.tracks.slice();
  const i = sandbox.rankNextIndex(4,sandbox.sessionPlayed,new Set());
  assert(i>=0 && i!==4);
});
test('Respeta exclusión de canción', () => {
  reset(5);
  const i = sandbox.rankNextIndex(0,sandbox.sessionPlayed,new Set([1,2,3]));
  assert.equal(i,4);
});
test('Evita bloqueo cuando la única no escuchada está excluida', () => {
  reset(5);
  const played = sandbox.tracks.slice(0,4);
  // El candidato 4 está reservado/excluido; otros 1..3 ya sonaron.
  const i = sandbox.rankNextIndex(0,played,new Set([4]));
  assert(i>=0 && i!==0 && i!==4,'El selector quedó sin candidato');
});
test('Organic Mix elige una no escuchada', () => {
  reset(5);
  const i = sandbox.proSimilarNext();
  assert(i>=1 && i<5);
});
test('Organic Mix no repite antes de terminar vuelta', () => {
  reset(5);
  sandbox.sessionPlayed = sandbox.tracks.slice(0,4);
  const i = sandbox.proSimilarNext();
  assert.equal(i,4);
});
console.log('\nResultado: '+pass+' OK, '+fail+' fallas');
if (fail) process.exitCode = 1;
