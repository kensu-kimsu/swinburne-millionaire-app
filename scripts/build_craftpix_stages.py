"""Compose the 15 playable maps from the supplied Craftpix packs.
Usage: python scripts/build_craftpix_stages.py --packs ../craftpix
The same authored floor grid is used by app.py and the browser's collisions.
"""
import argparse,json,random,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stage_layouts import STAGES,WIDTH,HEIGHT
OUT=ROOT/'static/assets/pixel'

def build_stages(packs):
 def pack(code):return next(packs.glob('*'+code+'*'))
 dungeon=pack('169442');undead=pack('695666');cursed=pack('958568');battle=pack('776320')
 sheets=[Image.open(dungeon/'PNG/walls_floor.png').convert('RGBA'),Image.open(undead/'PNG/Ground_rocks.png').convert('RGBA'),Image.open(cursed/'PNG/Ground.png').convert('RGBA')]
 objects=Image.open(dungeon/'PNG/Objects.png').convert('RGBA')
 water=Image.open(dungeon/'PNG/water_detilazation_v2.png').convert('RGBA')
 def cell(sheet,x,y):return sheet.crop((x*16,y*16,(x+1)*16,(y+1)*16))
 def prop(theme,kind):
  if theme==0:
   return objects.crop({'crates':(40,64,64,96),'barrels':(96,64,112,96),'pots':(192,64,208,96)}[kind])
  prefixes={'grave':'Grave_shadow1_9','crystal':'Crystal_shadow1_1','dead_tree':'Dead_tree_shadow1_1','ruin':'Ruin_shadow1_2','bones':'Pile_sculls_shadow1',
            'eye_plant':'Eye_plant_shadow1_1','jaws_plant':'Jaws_plant_shadow1_2','tentacles':'Tentacle_plant_shadow1_1','meat_flower':'Meat_flower_shadow1_2','eye_rock':'Rock_eyes_shadow1_2'}
  source=undead if theme==1 else cursed
  prefix=prefixes[kind] if kind!='ruin' or theme==1 else 'Ruins_shadow1_3'
  paths=list((source/'PNG').glob('Objects_separ*/*'))
  path=next(p for p in paths if p.stem==prefix)
  return Image.open(path).convert('RGBA')
 def paste_prop(canvas,image,x,y,max_size=(40,52)):
  image=image.crop(image.getbbox());image.thumbnail(max_size,Image.Resampling.NEAREST)
  canvas.alpha_composite(image,(round(x-image.width/2),round(y-image.height)))
 for stage in STAGES:
  number=stage['stage'];theme=(number-1)//5;variant=(number-1)%5;boss=variant==4
  rand=random.Random(3100+number);sheet=sheets[theme];mask=stage['walk_tiles']
  canvas=Image.new('RGBA',(WIDTH*16,HEIGHT*16),('#191a29','#121e20','#211820')[theme]);draw=ImageDraw.Draw(canvas)
  # Textured floor cells, never wall fragments on an apparently walkable path.
  floor_choices=([(1,10)]*12+[(0,21),(1,21),(1,22)],[(2,2)]*16+[(7,0)],[(18,8)]*18+[(16,8)])
  for y,row in enumerate(mask):
   for x,v in enumerate(row):
    if v=='1':
     ix,iy=rand.choice(floor_choices[theme]);canvas.alpha_composite(cell(sheet,ix,iy),(x*16,y*16))
  # Continuous cracked-stone trails make the outdoor walking routes legible.
  if theme==1:
   for x,y,w,h in (*__import__('stage_layouts').CONNECTORS[variant],):
    for row in range(y+1,y+h-1):
     for col in range(x+1,x+w-1):
      if mask[row][col]=='1':canvas.alpha_composite(cell(sheet,2,9),(col*16,row*16))
  # Pools have actual water detail and an explicit nonwalkable grid footprint.
  for x,y,w,h in stage['pits']:
   draw.rectangle((x*16,y*16,(x+w)*16-1,(y+h)*16-1),fill=('#23566d','#286941','#3b253b')[theme])
   for py in range(y*16,(y+h)*16,16):
    for px in range(x*16,(x+w)*16,32):
     ripple=water.crop((0,0,32,16))
     if theme: ripple=ImageEnhance.Color(ripple).enhance(.15)
     ripple=ripple.crop((0,0,min(32,(x+w)*16-px),min(16,(y+h)*16-py)))
     canvas.alpha_composite(ripple,(px,py))
  # Edge tiles on blocked cells make the walking boundaries visible. Dungeon
  # uses stone; outdoors uses the pack's cliff faces and broken root edges.
  def floor(x,y):return 0<=y<HEIGHT and 0<=x<WIDTH and mask[y][x]=='1'
  for y in range(HEIGHT):
   for x in range(WIDTH):
    if floor(x,y):continue
    neighbours=[floor(x,y+1),floor(x,y-1),floor(x+1,y),floor(x-1,y)]
    if not any(neighbours):continue
    if theme==0:
     tile=cell(sheet,1,3)
     canvas.alpha_composite(tile,(x*16,y*16))
     if neighbours[0]:draw.line((x*16,y*16+15,x*16+15,y*16+15),fill='#292b40',width=2)
    else:
     if neighbours[1]:
      # Three native cliff/root pieces form a connected drop below the floor.
      for depth in range(3):
       if y+depth>=HEIGHT or floor(x,y+depth):break
       tile=cell(sheet,16 if theme==1 else 8,(1+depth) if theme==1 else (4+depth))
       canvas.alpha_composite(tile,(x*16,(y+depth)*16))
     elif neighbours[0]:
      # A narrow dark rim does not pretend to be another walkable floor tile.
      draw.line((x*16,y*16+15,x*16+15,y*16+15),fill=('#4b5551','#653530')[theme-1],width=2)
     else:
      tile=cell(sheet,5 if neighbours[2] else 9,2 if theme==1 else 4)
      canvas.alpha_composite(tile,(x*16,y*16))
  # Dress the dungeon walls with alcoves, door niches, sacks and treasures.
  if theme==0:
   arch=sheet.crop((48,288,80,336))
   for x,y in ((7,3),(29,3),(7,14),(29,14)):
    if floor(x,y):canvas.alpha_composite(arch,(x*16-8,y*16-31))
   for x,y in ((4.5,2.0),(14.5,2.0)):
    # Fixture and the animated flame above it share this exact foot point.
    draw.rectangle((round(x*32)-3,round(y*32)-4,round(x*32)+3,round(y*32)+3),fill='#765447')
  # Native sprites preserve their proportions; each collision ellipse sits
  # under the visibly solid base rather than blocking the entire canopy.
  for item in sorted(stage['props'],key=lambda p:p['y']):
   im=prop(theme,item['kind']);foot_x=(item['x']+item['w']/2)*32;foot_y=(item['y']+item['h']/2)*32
   draw.ellipse((foot_x-10,foot_y-3,foot_x+10,foot_y+4),fill=('#383a51','#36403a','#6b3936')[theme])
   paste_prop(canvas,im,foot_x,foot_y+3)
  # Small, flat debris belongs to the floor and intentionally has no collision.
  if theme:
   details=Image.open((undead if theme==1 else cursed)/('PNG/Details.png' if theme==1 else 'PNG/details.png')).convert('RGBA')
   for _ in range(38):
    x=rand.randrange(2,34);y=rand.randrange(3,21)
    if not floor(x,y):continue
    patch=details.crop((0,0,16,16))
    if rand.random()<.5:patch=details.crop((32,16,48,32))
    canvas.alpha_composite(patch,(x*16,y*16))
  if boss:
   cx,cy=288,176
   colour=('#7592a9','#84b67a','#cb8067')[theme]
   draw.ellipse((cx-87,cy-69,cx+87,cy+69),outline=colour,width=2)
   draw.ellipse((cx-75,cy-57,cx+75,cy+57),outline=colour,width=1)
   for dx,dy in ((0,-61),(0,61),(-80,0),(80,0)):
    draw.polygon(((cx+dx,cy+dy-5),(cx+dx+4,cy+dy),(cx+dx,cy+dy+5),(cx+dx-4,cy+dy)),outline=colour)
  exit_x,exit_y=stage['exit'];foot=(exit_x*32,exit_y*32)
  if theme==0:door=sheet.crop((80,288,112,336))
  else:
   folder=(undead if theme==1 else cursed)/'PNG'
   name='Scull_door_shadow1' if theme==1 else 'Rock3_shadow1_1'
   door=Image.open(next(p for p in folder.glob('Objects_separ*/*') if p.stem==name)).convert('RGBA')
  paste_prop(canvas,door,*foot,max_size=(44,48))
  # Small open threshold keeps the portal's centre and the door's foot aligned.
  draw.line((foot[0]-10,foot[1]+2,foot[0]+10,foot[1]+2),fill=('#91a7b5','#81ad86','#c27e67')[theme],width=2)
  canvas.save(OUT/f'level-{number:02}.png',optimize=True)
 # Side-view paintings keep fights separate from top-down exploration maps.
 for theme,bg in enumerate((2,4,3),1):
  im=Image.open(battle/f'PNG/Battleground{bg}/Pale/Battleground{bg}.png').convert('RGB')
  im=im.resize((640,360),Image.Resampling.NEAREST)
  if theme==3:
   im=Image.blend(im,Image.new('RGB',im.size,'#5e292e'),.28)
  im.save(OUT/f'battle-{theme}.png',optimize=True)
 for code,root in [('dungeon',dungeon),('undead',undead),('cursedland',cursed),('battlegrounds',battle)]:
  licence=next(root.glob('*icense.txt'));(OUT/f'craftpix-{code}-license.txt').write_bytes(licence.read_bytes())
 (OUT/'stage-layouts.json').write_text(json.dumps(STAGES,indent=2))
 credits=ROOT/'ASSET_CREDITS.md';text=credits.read_text()
 if 'Craftpix' not in text:
  text+='\n- Craftpix — supplied Free 2D Top Down Pixel Dungeon, Free Undead Tileset, Free Cursed Land Tileset and Free Pixel Art Fantasy 2D Battlegrounds. Source: https://craftpix.net/. Supplied license notices are included beside the selected runtime images.\n'
  credits.write_text(text)
 print('Built 15 Craftpix stages and three side-view battle backgrounds')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packs',type=Path,default=ROOT.parent/'craftpix')
 build_stages(parser.parse_args().packs)
