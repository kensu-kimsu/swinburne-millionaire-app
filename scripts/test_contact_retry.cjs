const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('templates/index.html','utf8');
const code=html.slice(html.indexOf('function beginBattleContact('),html.indexOf('async function tickRoaming('))+
 html.slice(html.indexOf('async function moveDungeon('),html.indexOf('async function fetchQuestion('));
let reply,requests=[],overlay=false,entered=false;
const enemy={uid:'s1-e0',x:2.7,y:5,kind:'ENEMY',enemy_id:'spam_bot',defeated:false};
const c=vm.createContext({Math,performance:{now:()=>32},setTimeout:fn=>fn(),
 document:{getElementById:id=>({querySelector:()=>({textContent:''}),classList:{contains:()=>false,toggle(){},remove(){if(id==='battle-transition')overlay=true;},add(){if(id==='battle-transition')overlay=false;}}})},
 requestAnimationFrame(){},walkableLocal:()=>true,positionActors(){},syncArenaHud(){},playEffect(){},
 postJson:async(url,payload)=>{requests.push(payload);return new Promise(r=>reply=r);},
 processGameState:async()=>{entered=true;}, dungeonScene:{enemies:[enemy]},
 heroPosition:{x:1.5,y:5},confirmedHeroPosition:{x:1.5,y:5},dungeonMoving:false,tickBusy:false,
 encounterPending:false,contactEnemyUid:null,contactRetryAfter:0,battleEntering:false,contactStartedAt:0,
 heldKeys:new Set(),joystick:{x:0,y:0},moveInput:{x:0,y:0},lastFrame:0,lastMoveSent:0,lastMoveAt:0,lastSceneFrame:0});
vm.runInContext(code,c);
(async()=>{
 c.moveDungeon(); // Request leaves before the hero touches the enemy.
 c.heroPosition.x=2;c.movementFrame(16);assert.ok(overlay);
 assert.equal(requests.length,1,'wait for the existing movement request');
 reply({status:'moved',pending:'dungeon',dungeon:{player:{x:1.5,y:5},enemies:[{...enemy,x:3.4}]}});
 await new Promise(r=>setImmediate(r));
 assert.ok(overlay,'an older reply cannot cancel contact');assert.equal(c.contactEnemyUid,enemy.uid);
 c.movementFrame(32);assert.equal(requests[1].contact_uid,enemy.uid);
 reply({status:'moved',pending:'dungeon',dungeon:{player:{x:1.78,y:5},enemies:[{...enemy,x:3.5}]}});
 await new Promise(r=>setImmediate(r));
 assert.ok(overlay,'partial server movement must finish syncing instead of repeating the banner');
 c.movementFrame(48);assert.equal(requests[2].contact_uid,enemy.uid);
 reply({status:'encounter_started',pending:null,question:'Ready',enemy:{}});
 await new Promise(r=>setImmediate(r));
 assert.ok(entered);assert.equal(overlay,false);assert.equal(c.contactEnemyUid,null);
 console.log('Older reply, capped movement, persistent target and successful battle regression passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
