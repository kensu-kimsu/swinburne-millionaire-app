const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('templates/index.html','utf8');
const sound=html.slice(html.indexOf('function updateSoundButton('),html.indexOf('function syncMusic('));
const tracks={}; let attempts=0,blocked=true;
for(const id of ['music-menu','music-explore','music-final-boss']) tracks[id]={id,src:id+'.wav',dataset:{},paused:true,currentTime:0,
 getAttribute(){return this.src;},setAttribute(k,v){this.src=v;},pause(){this.paused=true;},play(){attempts++;if(blocked)return Promise.reject(Error('gesture needed'));this.paused=false;return Promise.resolve();}};
const button={setAttribute(){}};
const c=vm.createContext({audio:id=>tracks[id],currentMusic:null,soundEnabled:true,effectsUnlocked:false,
 document:{getElementById:id=>id==='sound-toggle'?button:{classList:{add(){}}},querySelectorAll:()=>[]}});
vm.runInContext(sound,c);
(async()=>{
 c.setMusic('music-menu');await new Promise(r=>setImmediate(r));assert.equal(button.textContent,'Enable sound');
 blocked=false;c.awakenSound();await new Promise(r=>setImmediate(r));assert.equal(button.textContent,'Sound on');
 c.setMusic('music-explore');await new Promise(r=>setImmediate(r));assert.equal(tracks['music-menu'].src,'music-explore.wav');
 assert.equal(tracks['music-explore'].paused,true,'reuse the gesture-unlocked player');
 c.setMusic('music-menu');await new Promise(r=>setImmediate(r));assert.equal(tracks['music-menu'].src,'music-menu.wav','preserve original menu source');
 c.setMusic('music-final-boss');await new Promise(r=>setImmediate(r));assert.equal(tracks['music-menu'].volume,.34);
 c.soundEnabled=false;c.setMusic('music-explore');assert.equal(tracks['music-menu'].paused,true);
 console.log('Audio failure recovery, shared player, source switching and mute checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
