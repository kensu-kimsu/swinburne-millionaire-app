const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const template=fs.readFileSync('templates/index.html','utf8');
const start=template.indexOf('        function showAnswerResult('),end=template.indexOf('        function cancelAutoContinue()',start);
const classes=()=>({values:new Set(['hidden']),add(...names){names.forEach(n=>this.values.add(n));},remove(...names){names.forEach(n=>this.values.delete(n));}});
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{classList:classes(),textContent:'',innerHTML:''});return nodes.get(id);};
let animations=[],continues=0,summaries=0;
const c=vm.createContext({document:{getElementById:node,querySelector:()=>node('panel')},
 currentState:{hp:12,enemy:{hp:8,max_hp:8}},heartMarkup:()=>'',renderState:()=>{},renderEnemy:()=>{},
 performCombat:()=>new Promise(resolve=>animations.push(resolve)),playCombatAudio:()=>{},buildTurnMessage:()=>'',
 continueRun:()=>{continues++;},beginAutoContinue:()=>{summaries++;}});
vm.runInContext(template.slice(start,end),c);
(async()=>{
 c.showAnswerResult({status:'answered',hp:11,max_hp:12,is_correct:true,damage_dealt:2,enemy:{hp:6}},'A');
 assert.equal(continues,0,'wait for physical strike before next question');
 assert.equal(node('feedback').classList.values.has('hidden'),true,'no turn-summary overlay');
 animations.shift()();await Promise.resolve();
 assert.equal(continues,1);assert.equal(summaries,0);
 c.showAnswerResult({status:'enemy_defeated',hp:12,max_hp:12,is_correct:true,defeated_enemy:'Goblin'},'A');
 assert.equal(node('feedback').classList.values.has('hidden'),true,'summary waits for final strike');
 animations.shift()();await Promise.resolve();
 assert.equal(continues,1);assert.equal(summaries,1);
 assert.equal(node('feedback').classList.values.has('hidden'),false);
 assert.equal(node('panel').classList.values.has('turn-resolved'),true);
 console.log('Fluid question progression waits for strikes; only completed battles display a summary');
})().catch(e=>{console.error(e);process.exitCode=1;});
