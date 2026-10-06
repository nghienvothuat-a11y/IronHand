"""Exterior public realm: checker plaza, shophouses, pools and entrance."""
c=collection('EMP_20_Site_and_landscape');ground=Mesh();roads=Mesh();paving=Mesh();paint=Mesh();pool=Mesh();furniture=Mesh()
ground.box((15,0,-.8),(470,594,1.6),'grass')
# Perimeter roads and the land-side boulevard.
roadloop=[(-208,-280),(178,-280),(189,-306),(204,-313),(231,-313),(244,-300),(244,-220),(234,-198),(234,280),(-208,280)]
roads.joined_ribbon(roadloop,11,.14,'asphalt')
paving.joined_ribbon(roadloop,15,.12,'pale')
roads.box((-238,0,-.04),(28,1550,.15),'asphalt')
ground.box((-239,0,.12),(3,1550,.25),'grass')
paving.box((-219,0,.1),(4,800,.22),'stone')
for yy in range(-760,780,12):
    for xx in (-246,-231):paint.box((xx,yy,.064),(.14,5,.01),'paint')
for idx in range(len(roadloop)):
    a=Vector(roadloop[idx]);b=Vector(roadloop[(idx+1)%len(roadloop)]);d=b-a;length=d.length;u=d.normalized()
    for j in range(int(length//12)):
        p=a+u*(6+j*12);paint.box((p.x,p.y,.22),(4,.13,.01),'paint',math.atan2(d.y,d.x))
# Entry drives, pedestrian axis, beach plaza.
for yy in (-85,85):roads.box((-194,yy,.16),(32,9,.14),'asphalt')
paving.box((0,0,.13),(413,22,.2),'pale')
for yy in (-13,13):paving.box((0,yy,.24),(414,1.1,.1),'dark_paving')
paving.box((202,0,.1),(64,58,.22),'pale')
# Concentric radial chess paving, with fine separating joints.
plaza=(-3,0);R=49
paving.disk(plaza,58,.13,'grass')
paving.disk(plaza,54,.21,'pale')
paving.disk(plaza,51,.24,'dark_paving')
for ring in range(8):
    r0=max(.4,ring*R/8);r1=(ring+1)*R/8-.085
    for j in range(40):
        a=j*2*math.pi/40+.0008;b=(j+1)*2*math.pi/40-.0008
        # Slight radial offset makes the plaza fan pattern visible from the air.
        pts=[(plaza[0]+r*math.cos(t),r*math.sin(t),.27) for r,t in [(r0,a),(r1,a),(r1,b),(r0,b)]]
        paving.face(pts, 'pale' if (ring+j)%2 else 'dark_paving')
paving.disk(plaza,3,.28,'pale',48)
for r in (51.7,53.5):
    pts=[(plaza[0]+r*math.cos(t*2*math.pi/128),r*math.sin(t*2*math.pi/128)) for t in range(128)]
    paving.ribbon(pts,.16,.28,'metal',True)
for sign in (-1,1):
    # Curved promenade encircling each courtyard.
    for sp in [p for p in PARAMS['towers'] if p['cy']*sign>0]:
        cx,cy=sp['cx'],sp['cy']
        pts=[(cx+29+53*math.cos(j*2*math.pi/120),cy+67*math.sin(j*2*math.pi/120)) for j in range(120)]
        paving.ribbon(pts,3,.22,'pale',True)
        # Link the lobby to the centre garden and pool.
        paving.ribbon([(cx-42,cy),(cx-18,cy-8),(cx+15,cy)],3.8,.24,'stone')
        paving.ribbon([(cx+17,cy-68),(cx+29,cy-54),(cx+16,cy-35)],2.5,.24,'pale')
        paving.ribbon([(cx+18,cy+68),(cx+26,cy+49),(cx+18,cy+30)],2.5,.24,'pale')

# Shophouses: repeated white villas along the pedestrian avenue, exterior only.
shopcol=collection('EMP_30_Arena_Town_Exterior'); shops=Mesh();sglass=Mesh();sdetail=Mesh()
shop_positions=[]
for yy in (-35,35):
    for xx in (-174,-143,-112,-81,77,109,141):shop_positions.append((xx,yy))
for group,(xx,yy) in enumerate(shop_positions):
    width=25;depth=24;h=13.2
    shops.box((xx,yy,h/2+.3),(width,depth,h),'ivory')
    # Recessed panels wrap all four exterior faces.
    for side in (-1,1):
        for floor in range(3):
            z=2.2+floor*3.6
            for offset in (-8,-2.7,2.7,8):
                shops.box((xx+offset,yy+side*(depth/2+.18),z),(4.4,.22,2.9),'black')
                sglass.box((xx+offset,yy+side*(depth/2+.32),z),(3.75,.10,2.5),'glass')
                sdetail.box((xx+offset,yy+side*(depth/2+.42),z),(.09,.09,2.5),'metal')
            if floor>0:
                shops.box((xx,yy+side*12.7,z-1.6),(25.5,2,.24),'ivory')
                sdetail.box((xx,yy+side*13.6,z-.95),(24.8,.10,.84),'rail')
                sdetail.box((xx,yy+side*13.65,z-.5),(25,.11,.10),'ivory')
        for oo in (-8,0,8):
            for floor in range(3):
                sglass.box((xx+side*12.55,yy+oo,2.2+floor*3.6),(.1,5,2.5),'glass_light')
    # Roof terraces, cuboid pergolas, recessed penthouse and planter edging.
    shops.box((xx,yy,13.65),(25.8,24.7,.35),'ivory')
    shops.box((xx,yy,13.88),(23,21.5,.12),'roof')
    for off in (-8,0,8):
        shops.box((xx+off,yy,15.2),(6.3,10,2.8),'ivory')
        sglass.box((xx+off,yy-5.08,15.2),(4.8,.08,2.1),'glass')
        for yoff in (-9,9):
            for xoff in (-2.9,2.9):shops.box((xx+off+xoff,yy+yoff,15.3),(.22,.22,2.8),'ivory')
            for slat in range(6):sdetail.box((xx+off,yy+yoff+(slat-2.5)*.55,16.7),(6.1,.19,.19),'ivory')
    paving.box((xx,yy,.25),(28,28,.30),'stone')
    for sign in (-1,1):
        for off in (-7.5,7.5):
            furniture.box((xx+off,yy+sign*15,.75),(3.5,1.25,.9),'ivory')
            furniture.box((xx+off,yy+sign*15,1.28),(3.25,1.05,.24),'grass')
shops.object('Arena_Town_white_shells',shopcol);sglass.object('Arena_Town_glazing',shopcol);sdetail.object('Arena_Town_terraces_pergolas',shopcol)
# Low ballroom roof tucked behind the north-west shopping row.
ball=Mesh();ball.box((-111,61,5.3),(70,18,10),'ivory');ball.box((-111,61,10.45),(71,19,.4),'roof')
ball.object('Ballroom_external_shell',shopcol)

# Pool contours, original geometry guided by the site map.
pool_specs=[]
for sp in PARAMS['towers']:
    sea='Sea' in sp['id'];cx=sp['cx']+(26 if sea else 25);cy=sp['cy']
    px,py={'A_Land_North':(22,11),'B_Sea_North':(39,22),'C_Land_South':(20,9.5),'D_Sea_South':(39,32)}[sp['id']]
    n=160;contour=[]
    for i in range(n):
        t=2*math.pi*i/n
        rr=1+({'A_Land_North':.05*math.cos(2*t),'B_Sea_North':.13*math.cos(6*t)+.045*math.sin(9*t),'C_Land_South':.08*math.cos(2*t),'D_Sea_South':.15*math.sin(3*t+.4)+.09*math.cos(5*t)}[sp['id']])
        contour.append((cx+px*rr*math.cos(t),cy+py*rr*math.sin(t)))
    # Fan triangles ensure the organic outline stays well-defined.
    for i in range(n):
        j=(i+1)%n;p=contour[i];q=contour[j]
        pool.face([(cx,cy,.40),(*p,.40),(*q,.40)],'water')
        pool.face([(cx,cy,.05),(*p,.05),(*q,.05)],'tile')
    pool.ribbon(contour,1.3,.43,'pale',True)
    paving.ribbon(contour,9,.23,'stone',True)
    pool_specs.append((cx,cy,px,py,sea))
    # Deck chairs, side tables and umbrella positions are outside the water.
    for i in range(24 if sea else 16):
        t=2*math.pi*i/(24 if sea else 16)
        x=cx+(px+8)*math.cos(t);y=cy+(py+8)*math.sin(t)
        angle=t+math.pi/2
        furniture.box((x,y,.66),(1,2.25,.20),'fabric',angle)
        furniture.box((x,y,.48),(1.05,2.45,.12),'wood',angle)
        for dx in (-.36,.36):
            for dy in (-.83,.83):
                xx=x+dx*math.cos(angle)-dy*math.sin(angle);yy=y+dx*math.sin(angle)+dy*math.cos(angle)
                furniture.box((xx,yy,.34),(.08,.08,.35),'metal',angle)
        # Raised backrest, geometrically tilted.
        xx=x-.78*math.sin(angle); yy=y+.78*math.cos(angle)
        furniture.beam((xx-.44*math.cos(angle),yy-.44*math.sin(angle),.84),(xx+.44*math.cos(angle),yy+.44*math.sin(angle),.84),.1,'fabric')

# Closed, lobed lazy river on the seaward side of the north pool.
river=[]
for i in range(240):
    t=i*math.tau/240;river.append((210+13.5*math.cos(t)+2.8*math.cos(3*t),155+49*math.sin(t)+3*math.sin(4*t)))
paving.ribbon(river,10,.20,'stone',True);pool.ribbon(river,6.5,.32,'pale',True);pool.ribbon(river,4.8,.39,'water',True)
# Separate circular spa attached to the landward end of the north swimming pool.
pool.disk((106,155),7.2,.45,'pale',64);pool.disk((106,155),5.8,.47,'water',64)
# Beach pedestrian promenade with timber boardwalks across the dunes.
paving.box((250,0,.18),(7,580,.3),'stone')
for yy in (-155,0,155):paving.box((279,yy,.13),(51,4,.25),'wood')

# Two elongated lens-shaped entrance canopies visible in the aerial reference.
entrance=Mesh()
for sign in (-1,1):
    cx,cy=-197,sign*37
    for j in range(48):
        t=-math.pi/2+j*math.pi/48;u=-math.pi/2+(j+1)*math.pi/48
        y1=cy+31*math.sin(t);y2=cy+31*math.sin(u)
        w1=9*max(0,math.cos(t))**.7;w2=9*max(0,math.cos(u))**.7
        z1=8+2.5*math.cos(t);z2=8+2.5*math.cos(u)
        entrance.face([(cx-w1,y1,z1),(cx+w1,y1,z1),(cx+w2,y2,z2),(cx-w2,y2,z2)],'glass_light')
        for side in (-1,1):entrance.beam((cx+side*w1,y1,z1),(cx+side*w2,y2,z2),.32,'ivory',8)
        if j%4==0:entrance.beam((cx-w1,y1,z1),(cx+w1,y1,z1),.14,'ivory',6)
    for yy in (cy-22,cy,cy+22):
        entrance.beam((cx,yy,.3),(cx,yy,10),.19,'ivory',8)
        entrance.beam((cx,yy,6),(cx-6,yy,10),.14,'ivory',6)
        entrance.beam((cx,yy,6),(cx+6,yy,10),.14,'ivory',6)
    paving.box((cx,cy,.25),(20,65,.35),'dark_paving')
entrance.object('Twin_entrance_canopies',c)

# Exterior service kiosks and parking bays.
service=Mesh()
for yy in (-253,253):
    for xx in (-153,-113,-73,96,136,176):
        paving.box((xx,yy,.2),(29,18,.25),'dark_paving')
        for dx in range(-12,15,3):paint.box((xx+dx,yy,.34),(.11,6,.015),'paint')
    for xx in (-185,20):
        service.box((xx,yy,2.3),(11,14,4.1),'ivory')
        service.box((xx,yy,4.42),(11.7,14.7,.25),'roof')
        service.box((xx+5.56,yy,2.2),(.08,8,2.6),'glass')
service.object('Service_pavilions',c)
for mesh,name in [(ground,'Resort_landform'),(roads,'Roads'),(paving,'Plazas_paths_and_pool_decks'),(paint,'Road_and_parking_markings'),(pool,'Pool_water_coping_and_lazy_river'),(furniture,'Outdoor_furniture')]:mesh.object(name,c)
save_stage('site_and_shophouses')
