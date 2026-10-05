"""Build Lantern Village using the supplied Pixel Crawler buildings and farm tiles."""
import json, random
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
PC=ROOT.parent/'asset-packs/Pixel Crawler - Free Pack/Environment'
OUT=ROOT/'static/assets/pixel'

def build():
    def sheet(path): return Image.open(PC/path).convert('RGBA')
    terrain=sheet('Tilesets/Floors_Tiles.png')
    walls=sheet('Structures/Buildings/Walls.png')
    roofs=sheet('Structures/Buildings/Roofs.png')
    props=sheet('Structures/Buildings/Props.png')
    farm=sheet('Props/Static/Farm.png')
    vegetation=sheet('Props/Static/Vegetation.png')
    trees=sheet('Props/Static/Trees/Model_01/Size_03.png')
    canvas=Image.new('RGBA',(576,352))
    rand=random.Random(731)
    grass=terrain.crop((16,176,32,192)); road=terrain.crop((96,176,112,192)); dirt=terrain.crop((176,176,192,192))
    for y in range(0,352,16):
        for x in range(0,576,16): canvas.alpha_composite(grass,(x,y))
    # A broad central square, branching lanes and clear access to every shop.
    paths=[(176,144,544,208),(256,160,320,352),(160,64,224,272),(368,80,416,304),(32,288,272,336)]
    for x1,y1,x2,y2 in paths:
        for y in range(y1,y2,16):
            for x in range(x1,x2,16): canvas.alpha_composite(road,(x,y))
    for i in range(130):
        x,y=rand.randrange(16,544),rand.randrange(40,330)
        if any(a-4<=x<=c+4 and b-4<=y<=d+4 for a,b,c,d in paths):continue
        canvas.alpha_composite(vegetation.crop((16,160,32,176)),(x,y))
    def house(x,y,glass=False):
        # Original timber/glass wall modules, roof and doors at native resolution.
        im=Image.new('RGBA',(112,144)); d=ImageDraw.Draw(im)
        d.rectangle((8,64,103,130),fill='#8d6842',outline='#322c26',width=3)
        for wx in (8,40,72): im.alpha_composite(walls.crop((0 if glass else 288,592,32 if glass else 320,640)),(wx,80))
        for wx in (8,100): d.rectangle((wx,66,wx+3,130),fill='#3a2c22')
        im.alpha_composite(props.crop((100,24,120,64)),(72,91))
        if glass: roof=roofs.crop((272,80,368,192))
        else: roof=roofs.crop((0,80,128,144)).resize((112,64),Image.Resampling.NEAREST)
        im.alpha_composite(roof,(8 if glass else 0,0 if glass else 24))
        return im
    canvas.alpha_composite(house(0,0), (40,8))
    canvas.alpha_composite(house(0,0), (424,0))
    # Central glass-roof merchant shop; counter and merchandise sit at the front.
    shop=house(0,0,True)
    canvas.alpha_composite(shop,(232,32))
    for x in (236,328):
        for y in (120,144):canvas.alpha_composite(farm.crop((160,32,176,64)),(x,y))
    counter=Image.new('RGBA',(96,48))
    for x in range(0,96,16):counter.alpha_composite(farm.crop((288,16,304,48)),(x,16))
    for x in (4,28,52,76):counter.alpha_composite(farm.crop((0,0,16,32)),(x,0))
    counter.save(OUT/'market-stall.png',optimize=True)
    # Fenced kitchen gardens: native cabbages, beets, scarecrows and produce baskets.
    gardens=[(32,192,176,272,80),(432,208,528,304,48)]
    for x1,y1,x2,y2,crop_y in gardens:
        for y in range(y1,y2,16):
            for x in range(x1,x2,16):canvas.alpha_composite(dirt,(x,y))
        for y in range(y1+8,y2-8,24):
            for x in range(x1+8,x2-8,24):canvas.alpha_composite(farm.crop((80,crop_y,96,crop_y+16)),(x,y))
        for x in range(x1,x2,16):
            for y in (y1-12,y2-4):canvas.alpha_composite(props.crop((0,176,16,208)),(x,y))
        for y in range(y1,y2,16):
            for x in (x1-6,x2-6):canvas.alpha_composite(props.crop((0,176,16,208)),(x,y))
        canvas.alpha_composite(farm.crop((240,24,272,80)),(x1+44,y1+4))
    # Edge trees vary foliage, with pocket gardens and stacked cargo by the houses.
    for i,(x,y) in enumerate([(0,-20),(144,-40),(352,-40),(528,-20),(0,90),(534,98),(0,260),(528,268),(176,238),(360,262)]):
        canvas.alpha_composite(trees.crop(((i%2)*48,0,(i%2+1)*48,96)),(x,y))
    for x,y in [(156,96),(408,120),(360,216),(224,224)]:
        canvas.alpha_composite(farm.crop((256,0,288,32)),(x,y))
    for x,y in [(72,144),(104,144),(336,240),(336,272)]:
        canvas.alpha_composite(farm.crop((160,32,176,64)),(x,y))
    # East gate aligns with the animated exit, away from the house footprint.
    canvas.alpha_composite(props.crop((32,24,64,64)),(496,136))
    canvas.save(OUT/'market.png',optimize=True)
    blocked=[(40,48,152,144),(232,48,344,184),(424,48,536,136),
             (26,184,182,284),(426,200,534,316),(176,320,224,336),(360,318,408,340)]
    grid=[]
    for row in range(22):
        line=''
        for col in range(36):
            x,y=col*16+8,row*16+8
            allowed=32<=x<544 and 48<=y<336 and not any(a<=x<c and b<=y<d for a,b,c,d in blocked)
            line+='1' if allowed else '0'
        grid.append(line)
    (OUT/'market-layout.json').write_text(json.dumps({'walk_tiles':grid,'spawn':[1.6,9.4],'exit':[16,5.5]}))
    return grid

if __name__=='__main__': build()
