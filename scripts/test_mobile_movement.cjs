// Exercise the actual inline client functions with delayed server responses.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('templates/index.html', 'utf8');
const frame = html.slice(html.indexOf('function movementFrame('), html.indexOf('async function tickRoaming('));
const move = html.slice(html.indexOf('async function moveDungeon('), html.indexOf('async function fetchQuestion('));
let resolveReply, sent, requests = 0, draws = 0;
const c = vm.createContext({Math, document: {getElementById: () => ({classList: {contains: () => false, toggle: () => {}}})},
 requestAnimationFrame: () => {}, walkableLocal: () => true,
 positionActors: () => draws++, syncArenaHud: () => {},
 postJson: async (url, body) => { requests++; sent = body; return new Promise(r => {resolveReply = r;}); },
 processGameState: async () => {}, enterBattle: async () => {}, touchingEnemy: () => false,
 beginBattleContact: () => {}, cancelBattleContact: () => {}, encounterPending: false, battleEntering: false,
 dungeonScene: {player: {x: 2, y: 5}}, heroPosition: {x: 2, y: 5}, confirmedHeroPosition: {x: 2, y: 5},
 dungeonMoving: false, tickBusy: false, heldKeys: new Set(['d']), joystick: {x:0,y:0},
 moveInput: {x:0,y:0}, lastFrame: 0, lastMoveSent: 0, lastMoveAt: 0, lastSceneFrame: 0});
vm.runInContext(frame + move, c);
(async () => {
 for (let t=16;t<=800;t+=16) c.movementFrame(t);
 assert.equal(requests, 1, 'only one movement request in flight');
 assert.ok(c.heroPosition.x - 2 < .88, 'prediction remains bounded');
 const before = c.heroPosition.x;
 resolveReply({pending:'dungeon', status:'moved', dungeon:{player:{...sent}}});
 await new Promise(r => setImmediate(r));
 assert.equal(c.heroPosition.x, before, 'delayed reply never snaps hero backward');
 c.heldKeys.clear();
 c.movementFrame(816);
 assert.equal(requests, 2, 'remaining predicted movement syncs after release');
 resolveReply({pending:'dungeon', status:'moved', dungeon:{player:{...sent}}});
 await new Promise(r => setImmediate(r));
 c.movementFrame(1000);
 assert.equal(requests, 2, 'stationary hero sends no redundant requests');
 assert.ok(draws <= 26, 'render rate is reduced while input remains responsive');
 c.heroPosition.x += .1;
 c.movementFrame(1200);
 resolveReply(null);
 await new Promise(r => setImmediate(r));
 assert.equal(c.dungeonMoving, false, 'failed request does not lock movement');
 c.movementFrame(1400);
 assert.equal(requests, 4, 'failed movement can retry');
 console.log('Delayed movement, release sync, draw budget, and recovery checks passed');
})().catch(e => {console.error(e);process.exitCode=1;});
