// Compare browser collision with the server on 47,520 world positions.
const fs=require('node:fs'),vm=require('node:vm'),cp=require('node:child_process'),assert=require('node:assert/strict');
const page=fs.readFileSync('templates/index.html','utf8');
const source=page.slice(page.indexOf('function walkableLocal('),page.indexOf('function followCamera('));
const context=vm.createContext({});vm.runInContext(source,context);
const cases=JSON.parse(cp.execFileSync(process.env.PYTHON||'python',['-c',`
import json
from app import walkable,FLOOR_BOUNDS
from stage_layouts import STAGES
output=[]
for stage in STAGES:
 d={'width':18,'height':11,'floor_bounds':FLOOR_BOUNDS,'walk_tiles':stage['walk_tiles'],
    'obstacles':[(p['x'],p['y'],p['w'],p['h']) for p in stage['props']]}
 expected=[walkable(d,.125+x*.25,.125+y*.25) for y in range(44) for x in range(72)]
 output.append({'dungeon':d,'expected':expected})
print(json.dumps(output))
`],{maxBuffer:2*1024*1024}).toString());
let count=0;
for(const [index,{dungeon,expected}] of cases.entries()){
 for(let y=0;y<44;y++)for(let x=0;x<72;x++){
  assert.equal(context.walkableLocal(dungeon,.125+x*.25,.125+y*.25),expected[y*72+x],`Stage ${index+1}, ${x},${y}`);count++;
 }
}
console.log(`Browser/server collision agrees at ${count.toLocaleString()} positions across all 15 stages`);
