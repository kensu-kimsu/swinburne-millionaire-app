"""Build the shipped game assets from the two user-supplied packs.
Usage: python scripts/build_pixel_assets.py --packs ../asset-packs
Only selected game assets are shipped; the original packs remain outside git.
"""
import argparse,json,random,sys,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import LEVEL_OBSTACLES,LEVEL_DOORS,FIRE_FIXTURES,LEVEL_WALLS
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'static/assets/pixel';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--packs',type=Path,default=ROOT.parent/'asset-packs')
packs=parser.parse_args().packs
PC=packs/'Pixel Crawler - Free Pack';FX=packs/'Super Pixel Effects Gigapack (Free Version)'
manifest={'actors':{},'effects':{},'icons':{}}

def save(im,name):
 im.save(OUT/name,'PNG',optimize=True)
 return '/static/assets/pixel/'+name

def actor(name,folder,tint=None):
 record={}
 for action in ('Idle','Run','Death'):
  files=sorted((PC/folder/action).glob('*.png'))
  if not files:continue
  im=Image.open(files[0]).convert('RGBA')
  aseprite=next((PC/folder/action).glob('*.aseprite'))
  magic,count,frame_width,frame_height=struct.unpack_from('<HHHH',aseprite.read_bytes(),4)
  if magic != 0xA5E0 or im.size != (frame_width*count,frame_height):
   raise ValueError(f'Invalid source atlas: {files[0]}')
  # Pack run/death cells include extra canvas padding. Keep a fixed native
  # footprint so switching from idle to running never clips or shrinks actors.
  size=64 if name=='merchant' or name.startswith('villager') else 32
  normalized=Image.new('RGBA',(size*count,size))
  for i in range(count):
   x=i*frame_width+(frame_width-size)//2
   normalized.alpha_composite(im.crop((x,frame_height-size,x+size,frame_height)),(i*size,0))
  im=normalized
  if tint:
   alpha=im.getchannel('A');im=ImageEnhance.Color(im).enhance(.35)
   overlay=Image.new('RGBA',im.size,tint);im=Image.blend(im,overlay,.25);im.putalpha(alpha)
  record[action.lower()]={'src':save(im,f'{name}-{action.lower()}.png'),'width':size,'height':size,'frames':count,'fps':8 if action=='Idle' else 12}
 manifest['actors'][name]=record

sources={
 'hero':"Entities/Npc's/Knight",'merchant':"Entities/Npc's/Citizen_F/Tavern_A",
 'villager_peasant':"Entities/Npc's/Citizen_F/Peasant_A",'villager_tavern':"Entities/Npc's/Citizen_F/Tavern_B",
 'spam_bot':'Entities/Mobs/Orc Crew/Orc',
 'phishing_email':'Entities/Mobs/Skeleton Crew/Skeleton - Rogue',
 'adware_bug':'Entities/Mobs/Orc Crew/Orc - Shaman',
 'botnet_node':'Entities/Mobs/Skeleton Crew/Skeleton - Warrior',
 'credential_thief':'Entities/Mobs/Orc Crew/Orc - Rogue',
 'malware_loader':'Entities/Mobs/Orc Crew/Orc - Warrior',
 'ransomware':'Entities/Mobs/Skeleton Crew/Skeleton - Mage',
 'insider_threat':"Entities/Npc's/Knight",'zero_day_exploit':"Entities/Npc's/Wizzard"}
for name,folder in sources.items():actor(name,folder,(120,65,180,255) if name=='insider_threat' else None)
# Characters in this pack intentionally separate body, hands and equipment.
# Composite original parts at native pixels; retain a fixed 48px frame canvas.
wood=Image.open(PC/'Weapons/Wood/Wood.png').convert('RGBA')
bone=Image.open(PC/'Weapons/Bone/Bone.png').convert('RGBA')
hands=Image.open(PC/'Weapons/Hands/Hands.png').convert('RGBA')
weapons={
 'blade':wood.crop((0,0,16,48)).resize((10,30),Image.Resampling.NEAREST),
 'staff':wood.crop((96,16,112,64)).resize((10,30),Image.Resampling.NEAREST),
 'bone':bone.crop((0,0,16,48)).resize((10,30),Image.Resampling.NEAREST)}
shield=wood.crop((128,0,144,16))
for name,record in manifest['actors'].items():
 if name=='merchant' or name.startswith('villager'):continue
 skeletal=name in ('phishing_email','botnet_node','ransomware')
 caster=name in ('adware_bug','ransomware','zero_day_exploit')
 hand=hands.crop((0,32 if skeletal else 64 if name in ('spam_bot','adware_bug','credential_thief','malware_loader') else 48,16,48 if skeletal else 80 if name in ('spam_bot','adware_bug','credential_thief','malware_loader') else 64))
 hand=hand.crop(hand.getbbox())
 weapon=weapons['staff' if caster else 'bone' if skeletal else 'blade']
 def equip(body,angle=0,swing=0,death=False):
  frame=Image.new('RGBA',(48,48));frame.alpha_composite(body,(8,16))
  if death:return frame
  held=weapon.rotate(angle,resample=Image.Resampling.NEAREST,expand=True)
  frame.alpha_composite(held,(min(48-held.width,32)+swing,8+abs(swing)))
  frame.alpha_composite(hand,(29+swing,35+abs(swing)))
  frame.alpha_composite(hand,(8,35))
  if not caster:frame.alpha_composite(shield,(1,31))
  return frame
 for action,meta in list(record.items()):
  original=Image.open(ROOT/meta['src'].lstrip('/')).convert('RGBA')
  sheet=Image.new('RGBA',(48*meta['frames'],48))
  for i in range(meta['frames']):
   body=original.crop((i*32,0,(i+1)*32,32))
   sheet.alpha_composite(equip(body,(-4 if i%2 else 0),0,action=='death'),(i*48,0))
  meta.update(src=save(sheet,f'{name}-{action}.png'),width=48,height=48)
 idle=Image.open(ROOT/record['idle']['src'].lstrip('/'))
 # Separate strike poses move the held weapon through a clear slash arc.
 original=Image.open(PC/sources[name]/'Idle'/next((PC/sources[name]/'Idle').glob('*.png')).name).convert('RGBA').crop((0,0,32,32))
 sheet=Image.new('RGBA',(48*8,48))
 for i,angle in enumerate((0,15,35,-25,-65,-85,-35,0)):
  sheet.alpha_composite(equip(original,angle,0),(i*48,0))
 record['attack']={'src':save(sheet,name+'-attack.png'),'width':48,'height':48,'frames':8,'fps':16}

# Citizen animation folder uses Walk; retain the original four-frame idle.
for name in ('merchant',):
 if 'idle' not in manifest['actors'][name]:raise ValueError('Missing merchant idle')

boss=Image.open(OUT/'boss-source.png').convert('RGBA')
for row,name in enumerate(('phishing_king','ransomware_overlord','root_admin')):
 im=boss.crop((0,row*96,384,(row+1)*96))
 pixels=im.load()
 for y in range(im.height):
  for x in range(im.width):
   r,g,b,a=pixels[x,y]
   if r>150 and b>140 and g<140 and min(r,b)>g*1.45:pixels[x,y]=(0,0,0,0)
 meta={'src':save(im,name+'-idle.png'),'width':96,'height':96,'frames':4,'fps':5}
 manifest['actors'][name]={'idle':meta,'run':meta}

# Retain all source effect frames in compact horizontal sprite atlases.
effects={
 'strike':('Impacts','directional_impact_001','white'),
 'guard':('Fantasy Spells','spell_defense_up_001','blue'),
 'exploit':('Lightning','lightning_strike_001','purple'),
 'junk_toll':('Magic Bursts','directional_coin_burst_001','yellow'),
 'false_beacon':('Lightning','lightning_burst_001','blue'),
 'ad_bloom':('Fantasy Spells','spell_poison_001','green'),
 'node_bastion':('Fantasy Spells','spell_defense_up_001','blue'),
 'key_siphon':('Fantasy Spells','spell_absorb_001','purple'),
 'payload_burst':('Explosions','epic_explosion_001','orange'),
 'ransom_seal':('Fantasy Spells','spell_death_001','red'),
 'backdoor_cleave':('Impacts','directional_impact_004','purple'),
 'zero_rewrite':('Magic Bursts','round_sparkle_burst_001','blue'),
 'tsunami':('Magic Bursts','directional_bubble_burst_001','blue'),
 'petrify':('Fantasy Spells','spell_death_001','grey'),
 'meteor':('Explosions','epic_explosion_002','yellow'),
 'time_stop':('Sci-fi','scifi_warp_001','blue'),
 'heal':('Fantasy Spells','spell_heal_001','green'),
 'portal':('Sci-fi','scifi_warp_002','blue'),
 'fire':('Fire','fire_looping_003A','orange')}
for key,(category,type_name,color) in effects.items():
 variants=sorted((FX/'PNG'/category/type_name).glob('*'))
 chosen=next((v for v in variants if 'small' in v.name and color in v.name),None)
 chosen=chosen or next((v for v in variants if color in v.name),variants[0])
 files=sorted(chosen.glob('frame*.png'))
 frames=[Image.open(p).convert('RGBA') for p in files]
 w,h=frames[0].size
 sheet=Image.new('RGBA',(w*len(frames),h))
 for i,im in enumerate(frames):sheet.alpha_composite(im,(i*w,0))
 manifest['effects'][key]={'src':save(sheet,'fx-'+key+'.png'),'width':w,'height':h,'frames':len(frames),'fps':15,'source':str(chosen.relative_to(FX))}

tiles=Image.open(PC/'Environment/Tilesets/Dungeon_Tiles.png').convert('RGBA')
terrain=Image.open(PC/'Environment/Tilesets/Floors_Tiles.png').convert('RGBA')
furniture=Image.open(PC/'Environment/Props/Static/Furniture.png').convert('RGBA')
resources=Image.open(PC/'Environment/Props/Static/Resources.png').convert('RGBA')
esoteric=Image.open(PC/'Environment/Props/Static/Esoteric.png').convert('RGBA')
props=Image.open(PC/'Environment/Props/Static/Dungeon_Props.png').convert('RGBA')
floor_tiles=[tiles.crop((x,y,x+16,y+16)) for x,y in [(64,0),(80,0),(96,0),(64,16),(80,16),(96,16)]]
wall=tiles.crop((0,8,16,24));gate=tiles.crop((0,112,32,160))
rock=Image.open(PC/'Environment/Props/Static/Rocks.png').convert('RGBA').crop((64,16,96,48))
save(rock,'obstacle.png')
# A brass-bound supply chest assembled in the pack's native 16px palette.
chest=Image.new('RGBA',(16,16));c=ImageDraw.Draw(chest)
c.rectangle((1,4,14,14),fill='#241d1b');c.rectangle((2,5,13,13),fill='#815332')
c.rectangle((2,3,13,6),fill='#af7949');c.line((2,7,13,7),fill='#33291e')
for x in (3,11):c.rectangle((x,3,x+1,13),fill='#cead65')
c.rectangle((7,6,9,10),fill='#e5c479');c.point((8,8),fill='#403021')
save(chest,'chest.png')
# Full counter and shelving built from the original furniture, not a generated substitute.
stall=Image.new('RGBA',(96,64));d=ImageDraw.Draw(stall)
# A small timber shop with a striped canopy, shelves and a complete counter.
d.rectangle((7,14,88,56),fill='#342928');d.rectangle((10,17,85,45),fill='#51402e')
for y in (27,40):d.rectangle((10,y,85,y+2),fill='#ae7949')
for x in (7,86):d.rectangle((x,11,x+3,62),fill='#97663e')
for x in range(3,94,10):d.rectangle((x,3,x+9,13),fill='#916457' if x%20==3 else '#c29c64')
d.line((3,14,93,14),fill='#342928',width=2)
for x in range(8,88,24):
 stall.alpha_composite(furniture.crop((0,8,24,24)),(x,46))
for x in (14,38,62):
 stall.alpha_composite(esoteric.crop((0,16,16,32)),(x,13))
 stall.alpha_composite(esoteric.crop((16,32,32,48)),(x+5,27))
save(stall,'market-stall.png')
icon_cells=[(0,16),(16,16),(32,16),(80,16),(0,32),(16,32),(32,32),(80,32),(0,112),(16,112),(32,128),(48,128)]
for i,(ix,iy) in enumerate(icon_cells):
 icon=esoteric.crop((ix,iy,ix+16,iy+16))
 if not icon.getbbox():icon=resources.crop(((i%8)*16,0,(i%8)*16+16,16))
 if not icon.getbbox():icon=chest
 manifest['icons'][str(i)]=save(icon,f'icon-{i}.png')

for stage in range(1,17):
 market=stage==16;theme=(stage-1)//5;rand=random.Random(stage)
 canvas=Image.new('RGBA',(576,352),(13,16,25,255));draw=ImageDraw.Draw(canvas)
 for y in range(56,328,16):
  for x in range(32,544,16):
   tile=floor_tiles[rand.randrange(len(floor_tiles))].copy()
   if market:tile=terrain.crop((16,176,32,192))
   elif 6<=stage<=9:tile=ImageEnhance.Color(terrain.crop((16,176,32,192))).enhance(.3)
   elif theme>=1:
    alpha=tile.getchannel('A');shade=(58,49,71,255) if theme==1 else (85,41,35,255)
    tile=Image.blend(tile,Image.new('RGBA',tile.size,shade),.2);tile.putalpha(alpha)
   canvas.alpha_composite(tile,(x,y))
 for x in range(16,560,16):
  canvas.alpha_composite(wall,(x,40));canvas.alpha_composite(wall,(x,328))
 for y in range(56,328,16):
  canvas.alpha_composite(wall,(16,y));canvas.alpha_composite(wall,(544,y))
 door_x=14.45 if market else LEVEL_DOORS[stage-1]
 canvas.alpha_composite(gate,(round(door_x*32)-16,36))
 # The props and collision centers share the same geometry.
 if not market:
  for ox,oy,w,h in LEVEL_OBSTACLES[stage-1]:
   rw,rh=max(8,round(w*32)),max(8,round(h*32))
   canvas.alpha_composite(rock.resize((rw,rh),Image.Resampling.NEAREST),(round(ox*32),round(oy*32)))
  for x,y in FIRE_FIXTURES[stage-1]:
   # Out-of-floor fixtures sit on the surrounding dark border.
   draw.rectangle((round(x*32)-2,round(y*32)-3,round(x*32)+2,round(y*32)+2),fill='#b87f41')
 # Furnish each room: wall alcoves, carpets, grates, shelving, banners.
 for x in (48,144,240,336,432):
  canvas.alpha_composite(tiles.crop((32,112,64,160)),(x,8))
  canvas.alpha_composite(furniture.crop((0,8,24,24)),(x,332))
 if not market:
  for ox,oy,w,h in LEVEL_OBSTACLES[stage-1]:
   x,y=round(ox*32),round(oy*32)
   patch=tiles.crop((112,160,144,192)) if stage%3==0 else furniture.crop((0,24,16,48))
   canvas.alpha_composite(patch.resize((round(w*32),round(h*32)),Image.Resampling.NEAREST),(x,y))
  # Inlaid centre carpets are walkable decoration.
  if stage%5==0:
   danger=['#15455a','#473154','#612d28'][theme]
   draw.ellipse((175,100,401,300),fill=danger,outline='#a96a53',width=3)
   draw.ellipse((192,117,384,283),outline='#d4a377',width=2)
   for x in (184,360):
    canvas.alpha_composite(props.crop((96,0,112,24)),(x,105))
   for k in range(8):
    import math
    x=288+int(math.cos(k*math.pi/4)*74);y=200+int(math.sin(k*math.pi/4)*62)
    draw.polygon(((x,y-7),(x+4,y),(x,y+7),(x-4,y)),fill='#c48155')
   if theme==2:
    for x in (48,512):draw.rectangle((x,60,x+10,315),fill='#b94f28')
  else:
   carpet=tiles.crop((80,160,96,192))
   for y in range(94,286,32):canvas.alpha_composite(carpet,(280,y))
   for x,y in ((64,68),(496,68),(64,300),(496,300)):
    canvas.alpha_composite(furniture.crop((348,32,364,48)),(x,y))
 # Put solid obstacle furnishings on top of decorative inlays.
 if not market:
  for ox,oy,w,h in LEVEL_OBSTACLES[stage-1]:
   patch=props.crop((96,0,112,24)) if 6<=stage<=10 else furniture.crop((0,24,16,48))
   canvas.alpha_composite(patch.resize((round(w*32),round(h*32)),Image.Resampling.NEAREST),(round(ox*32),round(oy*32)))
  if 6<=stage<=9:
   tree_sheet=Image.open(PC/'Environment/Props/Static/Trees/Model_01/Size_03.png').convert('RGBA')
   for x in (0,535):
    for y in (40,150,255):canvas.alpha_composite(tree_sheet.crop((96,0,144,96)),(x,y))
 if market:
  # Town buildings stay north of the walking area; small citizens animate
  # along the perimeter. The merchant's physical shop occupies the centre.
  tree_sheet=Image.open(PC/'Environment/Props/Static/Trees/Model_01/Size_03.png').convert('RGBA')
  tree=tree_sheet.crop((0,0,48,96))
  for x in (0,530):
   for y in (30,150,260):canvas.alpha_composite(tree,(x,y))
  for bx in (70,210,360):
   draw.rectangle((bx,4,bx+90,48),fill='#97663e',outline='#2b2524',width=2)
   draw.polygon(((bx-5,22),(bx+45,0),(bx+95,22)),fill='#466c7a',outline='#a2b8aa')
   for wx in (bx+10,bx+60):
    canvas.alpha_composite(furniture.crop((32,152,48,176)),(wx,23))
  for x,y in ((60,130),(450,135),(110,250),(400,280)):
   canvas.alpha_composite(Image.open(OUT/'market-stall.png').resize((64,43),Image.Resampling.NEAREST),(x,y))
  for x in (160,350):
   for y in range(65,320,16):
    draw.rectangle((x,y,x+12,y+12),fill='#867359',outline='#554c3b')
 if not market:
  for ox,oy,w,h in LEVEL_WALLS[stage-1]:
   ww,hh=round(w*32),round(h*32)
   section=Image.new('RGBA',(ww,hh))
   for y in range(0,hh,16):
    for x in range(0,ww,16):section.alpha_composite(wall,(x,y))
   canvas.alpha_composite(section,(round(ox*32),round(oy*32)))
  for x,y in FIRE_FIXTURES[stage-1]:
   canvas.alpha_composite(furniture.crop((368,64,384,80)),(round(x*32)-8,round(y*32)-8))
 # Stage runes distinguish the 15 fixed rooms without introducing invisible walls.
 for k in range(stage%5+1):draw.rectangle((250+k*16,165,257+k*16,172),outline=['#667f79','#977bba','#ba683d'][min(theme,2)])
 save(canvas,'market.png' if market else f'level-{stage:02}.png')

# Title scene is assembled with the actual tiles and characters.
title=Image.open(OUT/'level-01.png').convert('RGBA')
for name,x,y in [('hero',265,205),('spam_bot',150,125),('phishing_email',415,180),('merchant',330,105)]:
 meta=manifest['actors'][name]['idle'];im=Image.open(ROOT/meta['src'].removeprefix('/')).crop((0,0,meta['width'],meta['height']))
 im.thumbnail((48,48),Image.Resampling.NEAREST);title.alpha_composite(im,(x,y))
save(title,'title-room.png');save(Image.open(OUT/'level-05.png'),'battle-room.png')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'effects-license.txt').write_bytes((FX/'license.txt').read_bytes())
(ROOT/'ASSET_CREDITS.md').write_text('''# Game asset credits\n\n- Pixel Crawler Free Pack 2.11 — Anokolisa. Source: https://anokolisa.itch.io/dungeon-crawler-pixel-art-asset-pack\n- Super Pixel Effects Gigapack Free Version 3.0.0 — Will Tice / unTied Games. Selected effects are integrated into the game at their original 15 FPS. See static/assets/pixel/effects-license.txt.\n- VT323 — Peter Hull; Silkscreen — Jason Kottke. SIL Open Font License; included under static/fonts.\n- Leviathan, Death and Dragon four-frame idle sprites — generated for this game using Pixel Crawler as the visual reference.\n\nThe supplied ZIP archives are not redistributed. These selected runtime assets form part of the game, not a reusable asset pack.\n''')
if (ROOT.parent/'craftpix').exists():
 from build_craftpix_stages import build_stages
 build_stages(ROOT.parent/'craftpix')
print('Built',len(list(OUT.glob('*.png'))),'pixel assets')
