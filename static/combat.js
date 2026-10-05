// A gesture-unlocked Web Audio mixer: music and SFX share one resumed context.
let gameAudioContext=null, gameMusicVoice=null, gameMusicRequest=0;
const decodedSounds=new Map(), effectVoices=new Set();
function unlockGameAudio() {
 const AudioEngine=window.AudioContext||window.webkitAudioContext;
 if(!AudioEngine)return false;
 try {
  gameAudioContext ||= new AudioEngine();
  gameAudioContext.resume().then(()=>setMusic(currentMusic||'music-menu')).catch(()=>updateSoundButton(false));
  return true;
 } catch(error){return false;}
}
async function decodedSound(id) {
 const element=audio(id);
 const src=element.dataset.source||element.getAttribute('src');
 if(!decodedSounds.has(src))decodedSounds.set(src,fetch(src).then(r=>{if(!r.ok)throw Error('Audio load');return r.arrayBuffer();}).then(b=>gameAudioContext.decodeAudioData(b)).catch(e=>{decodedSounds.delete(src);throw e;}));
 return decodedSounds.get(src);
}
function haltSpecificAudio(id) {for(const voice of effectVoices)if(voice.effect===id){try{voice.stop();}catch(error){}effectVoices.delete(voice);}}
function haltGameAudio(music=false) {
 for(const voice of effectVoices){try{voice.stop();}catch(error){}}effectVoices.clear();
 if(music){gameMusicRequest++;if(gameMusicVoice){try{gameMusicVoice.stop();}catch(error){}}gameMusicVoice=null;}
}
async function webEffect(id,loop=false) {
 if(!gameAudioContext||!soundEnabled)return;
 try {
  const buffer=await decodedSound(id);if(!soundEnabled)return;
  const source=gameAudioContext.createBufferSource(),gain=gameAudioContext.createGain();
  source.buffer=buffer;source.loop=loop;source.effect=id;gain.gain.value=.65;
  source.connect(gain).connect(gameAudioContext.destination);effectVoices.add(source);
  source.onended=()=>effectVoices.delete(source);source.start();
 }catch(error){updateSoundButton(false);}
}
async function webMusic(id) {
 if(!gameAudioContext||!soundEnabled)return;
 if(gameMusicVoice?.track===id)return;
 const requestId=++gameMusicRequest;
 try {
  const buffer=await decodedSound(id);if(requestId!==gameMusicRequest||!soundEnabled)return;
  if(gameMusicVoice){try{gameMusicVoice.stop();}catch(error){}}
  const source=gameAudioContext.createBufferSource(),gain=gameAudioContext.createGain();
  source.buffer=buffer;source.loop=true;source.track=id;gain.gain.value=.25;
  source.connect(gain).connect(gameAudioContext.destination);source.start();gameMusicVoice=source;
  updateSoundButton(gameAudioContext.state==='running');
 }catch(error){updateSoundButton(false);}
}
function heartMarkup(hp,max,small=false) {
 // Each full heart represents two HP; half hearts represent an odd remainder.
 const hearts=Math.ceil(max/2);
 return `<span class="heart-meter ${small?'small':''}" role="img" aria-label="${hp} of ${max} hit points">${Array.from({length:hearts},(_,i)=>`<i class="pixel-heart ${hp>=i*2+2?'full':hp>i*2?'half':'empty'}">♥</i>`).join('')}</span>`;
}
function updateCompactHud(data) {
 document.getElementById('player-hp').innerHTML=heartMarkup(data.hp,data.max_hp);
 document.getElementById('battle-player-hearts').innerHTML=heartMarkup(data.hp,data.max_hp,true);
 if(data.enemy)document.getElementById('battle-enemy-hearts').innerHTML=heartMarkup(data.enemy.hp,data.enemy.max_hp,true);
}
function openRelicBag() {
 if(!currentState||combatAnimating)return;
 document.getElementById('relic-bag').classList.remove('hidden');
 stopTimer();acceptingAnswers=true;
 const list=document.getElementById('relic-bag-items');list.replaceChildren();
 for(const item of currentState.inventory){
  const button=document.createElement('button');button.className='bag-item';
  button.innerHTML=`${gameAsset('item',item.id)}<b>${escapeHtml(item.name)} ×${item.quantity||1}</b><span>${escapeHtml(item.description)}</span>`;
  button.disabled=item.id==='backup'||!questionLoaded;
  button.onclick=async()=>{closeRelicBag();await useItem(item.id);};list.appendChild(button);
 }
 for(const relic of currentState.relics){
  const entry=document.createElement('div');entry.className='bag-item passive';
  entry.innerHTML=`${gameAsset('relic',relic.id)}<b>${escapeHtml(relic.name)} ×${relic.quantity||1}</b><span>PASSIVE · ${escapeHtml(relic.description)}</span>`;list.appendChild(entry);
 }
 if(!list.children.length)list.textContent='No relics collected yet.';
}
function closeRelicBag() {
 document.getElementById('relic-bag').classList.add('hidden');
 if(questionLoaded&&acceptingAnswers)resumeTimer();
}
let combatAnimating=false;
const battleSleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function combatAnnouncement(message) {
 const popup=document.getElementById('skill-announcement');popup.textContent=message;
 popup.classList.remove('hidden');clearTimeout(popup.hideTimer);
 popup.hideTimer=setTimeout(()=>popup.classList.add('hidden'),1600);
}
async function poseDuring(node,actor,action,duration) {
 const sprite=node.querySelector('.pixel-sprite');if(!sprite)return battleSleep(duration);
 const meta=PIXEL_ASSETS.actors[actor]?.[action]||PIXEL_ASSETS.actors[actor]?.idle;
 sprite.dataset.attacking='yes';sprite.setAttribute('viewBox',`0 0 ${meta.width} ${meta.height}`);
 const start=performance.now();
 await new Promise(resolve=>{function frame(t){updateAtlas(sprite.querySelector('image'),meta,t-start);if(t-start<duration)requestAnimationFrame(frame);else resolve();}requestAnimationFrame(frame);});
 delete sprite.dataset.attacking;updateAtlas(sprite.querySelector('image'),PIXEL_ASSETS.actors[actor].idle,performance.now());
}
async function strikeOpponent(side,actor,effect,label,melee=true) {
 const striker=document.getElementById(side==='hero'?'battle-hero':'enemy-icon');
 const target=document.getElementById(side==='hero'?'enemy-icon':'battle-hero');
 combatAnnouncement(label);
 if(melee){
  const a=striker.getBoundingClientRect(),b=target.getBoundingClientRect();
  const distance=b.left+b.width/2-a.left-a.width/2;
  const dx=distance-Math.sign(distance)*Math.min(55,(a.width+b.width)*.15);
  const travel=striker.animate([{transform:'translateX(0)'},{transform:`translateX(${dx}px)`}],{duration:420,easing:'ease-in',fill:'forwards'});
  await poseDuring(striker,actor,'run',420);
  playPixelEffect(effect,label,side==='hero'?'enemy':'hero');playEffect(side==='hero'?'snd-attack':'snd-enemy');
  const hit=target.animate([{transform:'translateX(0)'},{transform:`translateX(${Math.sign(dx)*10}px)`},{transform:'translateX(0)'}],{duration:220});
  await poseDuring(striker,actor,'attack',480);
  const retreat=striker.animate([{transform:`translateX(${dx}px)`},{transform:'translateX(0)'}],{duration:350,easing:'ease-out',fill:'forwards'});
  await poseDuring(striker,actor,'run',350);travel.cancel();retreat.cancel();hit.cancel();
 }else{
  playPixelEffect(effect,label,side==='enemy'&&['heal','guard','ad_bloom','zero_rewrite','node_bastion'].includes(effect)?'enemy':side==='hero'?'enemy':'hero');
  await poseDuring(striker,actor,'attack',800);
 }
}
async function performCombat(data,opponent) {
 combatAnimating=true;
 try {
  const id=opponent?.id||data.defeated_enemy_id;
  const enemyTurn=async()=>{
   const action=data.enemy_action;if(!action||action.canceled)return;
   const effect=action.pixel_effect||({attack:'strike',heavy_attack:'payload_burst',heal:'heal',defend:'guard',tsunami:'tsunami',meteor:'meteor',time_stop:'time_stop',petrify:'petrify',encrypt:'ransom_seal',jammer:'false_beacon'}[action.id]||'strike');
   await strikeOpponent('enemy',id,effect,`${action.first_strike?'FIRST STRIKE · ':''}${action.name}`,['attack','heavy_attack'].includes(action.id));
  };
  if(data.first_strike)await enemyTurn();
  if(data.player_acted!==false&&data.is_correct){
   if(data.combat_action==='defend'){combatAnnouncement('AEGIS GUARD');playPixelEffect('guard','GUARD','hero');await battleSleep(650);}
   else await strikeOpponent('hero','hero',data.combat_action==='exploit'?'exploit':'strike',data.combat_action==='exploit'?'ARCANE STRIKE':'BLADE STRIKE');
  }
  if(!data.first_strike)await enemyTurn();
  if(data.enemy_action?.canceled)combatAnnouncement(`${data.enemy_action.name} INTERRUPTED`);
  document.getElementById('battle-enemy-hearts').innerHTML=heartMarkup(data.enemy?.hp||0,opponent?.max_hp||1,true);
  updateCompactHud(data);
 } finally {combatAnimating=false;beginAutoContinue();}
}
function setupCompactBattle() {
 const question=document.querySelector('.question-card'),commands=document.getElementById('combat-actions');
 const menu=document.createElement('section');menu.className='command-menu';
 menu.appendChild(commands);menu.appendChild(document.querySelector('.actions'));
 const bagButton=document.createElement('button');bagButton.id='bag-button';bagButton.textContent='RELICS';bagButton.onclick=openRelicBag;commands.appendChild(bagButton);
 const panel=document.querySelector('.main-panel');panel.insertBefore(question,document.getElementById('enemy-card'));panel.appendChild(menu);
 // A floating, invisible thumb origin works anywhere on the exploration view.
 const surface=document.getElementById('dungeon-screen');let pointer=null,origin=null;
 surface.addEventListener('pointerdown',event=>{
  if(event.target.closest('button')||pointer!==null||surface.classList.contains('hidden'))return;
  pointer=event.pointerId;origin={x:event.clientX,y:event.clientY};surface.setPointerCapture(pointer);event.preventDefault();
 });
 surface.addEventListener('pointermove',event=>{
  if(event.pointerId!==pointer)return;
  const dx=event.clientX-origin.x,dy=event.clientY-origin.y,length=Math.hypot(dx,dy),radius=50;
  joystick=length<7?{x:0,y:0}:{x:dx/Math.max(radius,length),y:dy/Math.max(radius,length)};
  event.preventDefault();
 });
 const release=event=>{if(event.pointerId!==pointer)return;pointer=null;origin=null;joystick={x:0,y:0};setTimeout(moveDungeon,120);};
 for(const name of ['pointerup','pointercancel','lostpointercapture'])surface.addEventListener(name,release);
 window.addEventListener('blur',()=>{pointer=null;joystick={x:0,y:0};});
 for(const name of ['pointerup','click','keydown'])document.addEventListener(name,event=>{if(soundEnabled)unlockGameAudio();},{capture:true});
}
