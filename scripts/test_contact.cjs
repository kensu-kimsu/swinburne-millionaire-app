const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('templates/index.html','utf8');
const code=html.slice(html.indexOf('function beginBattleContact('),html.indexOf('async function tickRoaming('))+
 html.slice(html.indexOf('async function moveDungeon('),html.indexOf('async function fetchQuestion('));
let resolveReply,requests=0,overlay=false,entered=false;
const c=vm.createContext({Math,performance:{now:()=>32},setTimeout:fn=>fn(),
 document:{getElementById:id=>({classList:{contains:()=>false,toggle(){},remove(){if(id==='battle-transition')overlay=true;},add(){if(id==='battle-transition')overlay=false;}}})},
 requestAnimationFrame(){},walkableLocal:()=>true,positionActors(){},syncArenaHud(){},playEffect(){},
 postJson:async()=>{requests++;return new Promise(r=>resolveReply=r);},
 processGameState:async data=>{assert.ok(data.question);entered=true;c.movementFrame(64);assert.equal(requests,1);},
 dungeonScene:{enemies:[{x:2.76,y:5,kind:'ENEMY',enemy_id:'spam_bot',defeated:false}]},
 heroPosition:{x:2,y:5},confirmedHeroPosition:{x:2,y:5},dungeonMoving:false,tickBusy:false,
 encounterPending:false,battleEntering:false,contactStartedAt:0,heldKeys:new Set(['d']),joystick:{x:0,y:0},
 moveInput:{x:0,y:0},lastFrame:0,lastMoveSent:0,lastMoveAt:0,lastSceneFrame:0});
vm.runInContext(code,c);
(async()=>{
 c.movementFrame(16);c.movementFrame(32);
 assert.ok(overlay,'contact feedback is shown before the network reply');
 assert.equal(requests,1,'contact bypasses ordinary movement send interval');
 const atContact=c.heroPosition.x;c.movementFrame(48);
 assert.equal(c.heroPosition.x,atContact,'hero stops at contact');assert.equal(requests,1);
 resolveReply({status:'encounter_started',pending:null,enemy:{},question:'Ready',options:{A:'Test'}});
 await new Promise(r=>setImmediate(r));
 assert.ok(entered,'battle receives the first question directly');assert.equal(overlay,false);
 assert.equal(c.battleEntering,false);
 console.log('Immediate contact feedback, urgent request, movement freeze and battle-entry checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
