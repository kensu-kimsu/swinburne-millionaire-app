const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('static/combat.js','utf8');
let starts=0,stops=0,resumes=0;
class Context {
 constructor(){this.state='suspended';this.destination={};}
 resume(){resumes++;this.state='running';return Promise.resolve();}
 decodeAudioData(){return Promise.resolve({duration:1});}
 createBufferSource(){return {connect(){return this;},start(){starts++;},stop(){stops++;}};}
 createGain(){return {gain:{value:0},connect(){return this;}};}
}
const c=vm.createContext({window:{AudioContext:Context},audio:id=>({dataset:{},getAttribute:()=>id+'.wav'}),
 fetch:async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(1)}),currentMusic:'music-menu',soundEnabled:true,
 setMusic:id=>c.webMusic(id),updateSoundButton:()=>{}});
vm.runInContext(source,c);
const settle=()=>new Promise(r=>setImmediate(r));
(async()=>{
 assert.equal(c.unlockGameAudio(),true);await settle();await settle();assert.equal(resumes,1);assert.equal(starts,1);
 await c.webMusic('music-menu');assert.equal(starts,1,'reuse active music');
 await c.webMusic('music-boss');assert.equal(starts,2);assert.equal(stops,1,'stop previous track');
 await c.webEffect('snd-ticking',true);assert.equal(starts,3);c.haltSpecificAudio('snd-ticking');assert.equal(stops,2);
 c.soundEnabled=false;await c.webEffect('snd-attack');assert.equal(starts,3,'mute blocks new voices');c.haltGameAudio(true);assert.equal(stops,3);
 // Use actual attack travel logic with DOM rectangles. The striker moves to
 // touching distance, plays the strike, and returns to its starting position.
 const travels=[];const node=(left)=>({getBoundingClientRect:()=>({left,width:120}),animate:(frames)=>{travels.push(frames);return {cancel(){}};}});
 const hero=node(0),enemy=node(300);c.document={getElementById:id=>id==='battle-hero'?hero:enemy};
 c.combatAnnouncement=()=>{};c.poseDuring=async()=>{};c.playPixelEffect=()=>{};c.playEffect=()=>{};
 await c.strikeOpponent('hero','hero','strike','BLADE STRIKE');
 assert.equal(travels[0][1].transform,'translateX(264px)');assert.equal(travels[2][1].transform,'translateX(0)');
 console.log('Web Audio gesture, track reuse, mute, tick cleanup and physical combat movement passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
