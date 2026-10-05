"""Authored rooms and corridors, shared by the renderer and collision engine.
One cell is 16 artwork pixels / half a world unit. Props collide at their base.
"""
WIDTH, HEIGHT, CELL = 36, 22, .5
# Southwest entrance, northeast exit; broad connectors make loops and side rooms.
ROOMS = (
 ((2,14,10,7),(2,3,10,7),(15,7,8,10),(26,3,8,7),(26,14,8,7)),
 ((2,14,9,7),(2,3,9,7),(14,3,8,18),(26,3,8,7),(26,14,8,7)),
 ((2,14,11,7),(3,3,10,7),(15,10,8,10),(16,3,7,6),(26,3,8,9),(27,15,7,6)),
 ((2,14,9,7),(2,3,9,7),(14,7,9,9),(26,3,8,7),(26,14,8,7)),
 ((2,3,32,18),),
)
CONNECTORS = (
 ((5,8,4,9),(9,5,20,4),(9,15,20,4),(29,7,4,10),(18,5,4,13)),
 ((8,5,22,4),(8,15,22,4),(5,8,4,9),(29,7,4,10)),
 ((6,7,4,11),(10,15,19,4),(10,5,19,4),(18,6,4,10),(28,9,4,9)),
 ((5,7,4,11),(8,5,22,4),(8,15,22,4),(29,7,4,10),(18,5,4,13)),
 (),
)
NAMES = ('The Flooded Vault','Smuggler’s Barracks','The Broken Aqueduct','The Warden’s Keep','Leviathan’s Sanctum',
         'Bone Orchard','The Fallen Chapel','The Hollow Crypt','Gravekeeper’s Crossing','Death’s Cathedral',
         'Bloodroot Crossing','The Watching Grove','The Living Labyrinth','The Maw of Ruin','The Dragon’s Heart')

def stage_geometry(stage):
 variant=(stage-1)%5;theme=(stage-1)//5
 grid=[[False]*WIDTH for _ in range(HEIGHT)]
 for x,y,w,h in (*ROOMS[variant],*CONNECTORS[variant]):
  for row in range(y,y+h):
   for col in range(x,x+w):grid[row][col]=True
 # Cut themed pools/pits into broad chambers; routes stay at least four cells wide.
 pits=(((3,4,3,3),(29,16,3,3)),((3,4,3,3),(27,16,3,3)),
       ((4,4,3,3),(28,4,3,3)),((3,4,3,3),(28,16,3,3)),
       ((3,4,4,4),(25,4,4,4),(5,14,4,3),(29,15,4,4)))
 for x,y,w,h in pits[variant]:
  for row in range(y,y+h):
   for col in range(x,x+w):grid[row][col]=False
 # Prop bases avoid the entrance, main corridors, enemy and portal positions.
 positions=(((4,7),(9,3),(16,8),(21,15),(29,7),(32,14)),
            ((9,3),(3,8),(14,10),(21,8),(27,7),(32,14)),
            ((11,3),(3,8),(16,11),(22,16),(26,10),(33,15)),
            ((3,8),(10,3),(15,8),(22,14),(27,7),(33,14)),
            ((8,4),(26,4),(8,17),(26,17),(3,10),(32,10)))
 palettes=(('crates','barrels','pots','crates','barrels','pots'),
           ('grave','crystal','dead_tree','ruin','bones','grave'),
           ('eye_plant','jaws_plant','tentacles','meat_flower','eye_rock','ruin'))
 props=[]
 for index,(x,y) in enumerate(positions[variant]):
  if not grid[y][x]:continue
  kind=palettes[theme][(index+variant)%6]
  props.append({'kind':kind,'x':x*CELL,'y':y*CELL,'w':.8,'h':.6})
 # Additional furnishings hug room edges and share the same collision bases.
 for index,(rx,ry,rw,rh) in enumerate(ROOMS[variant]):
  for x,y in ((rx+1,ry+rh-2),(rx+rw-2,ry+2)):
   px,py=x*CELL,y*CELL
   if not grid[y][x] or any(abs(px-p['x'])<1 and abs(py-p['y'])<1 for p in props):continue
   if abs(px-1.6)<1 and abs(py-9.4)<1:continue
   if abs(px-16)<1 and abs(py-2.6)<1:continue
   props.append({'kind':palettes[theme][(index+variant+2)%6],'x':px,'y':py,'w':.8,'h':.6})
 # Different secondary set dressing within the same five room archetypes.
 return {'stage':stage,'name':NAMES[stage-1],'theme':('dungeon','undead','cursedland')[theme],
         'walk_tiles':[''.join('1' if v else '0' for v in row) for row in grid],
         'pits':pits[variant],'props':props,'spawn':(1.6,9.4),'exit':(16.0,2.6)}

STAGES=tuple(stage_geometry(stage) for stage in range(1,16))
