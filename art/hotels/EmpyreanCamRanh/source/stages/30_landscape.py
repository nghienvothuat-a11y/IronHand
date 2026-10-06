"""Instanced original coconut palms, planting, beach and exterior amenities."""
plants=collection('EMP_40_Palms_and_planting');env=collection('EMP_90_Render_context');amen=collection('EMP_45_Beach_amenities')
M['leaf_deep']=mat('Foliage_deep',(.036,.105,.021),.84)
M['leaf_yellow']=mat('Foliage_yellow_green',(.23,.33,.055),.84)
M['flower']=mat('Bougainvillea_rose',(.40,.065,.10),.84)

def leafmesh(variant):
    r=random.Random(556+variant);mesh=Mesh();h=10.5+variant*.6;lean=.45+variant*.22
    trunk=[]
    for j in range(27):
        t=j/26;trunk.append(Vector((lean*t*t,.19*math.sin(t*2),h*t)))
    for j in range(26):
        mesh.beam(trunk[j],trunk[j+1],.23*(1-j/40),'trunk',9)
        if j%2==0:mesh.beam(trunk[j],trunk[j]+Vector((0,0,.065)),.25*(1-j/40),'stone',9)
    top=trunk[-1]
    for j in range(17):
        a=j*2*math.pi/17+r.uniform(-.13,.13);L=r.uniform(4.6,6.3)
        f=Vector((math.cos(a),math.sin(a),0));side=Vector((-math.sin(a),math.cos(a),0))
        def stem(t):return top+f*(L*t)+Vector((0,0,2.9*t-4.3*t*t+.18))
        for q in range(14):mesh.beam(stem(q/14),stem((q+1)/14),.028*(1-q/17),'leaf_light',4)
        for q in range(2,37):
            t=q/38;mid=stem(t);length=(.35+1.1*math.sin(math.pi*t))*(1-.4*t)
            for sg in (-1,1):
                tip=mid+sg*side*length+f*(.24+.26*t)+Vector((0,0,-.26-.30*t))
                midleaf=(mid+tip)/2+Vector((0,0,.09))
                w=.15*(1-.50*t);material='leaf' if (q+j+variant)%3 else 'leaf_light'
                mesh.face([mid,midleaf-f*w,tip,midleaf+f*w],material)
    return mesh

templates=[]
for i in range(4):
    ob=leafmesh(i).object('Palm_template_'+str(i),plants)
    # Keep the prototype itself as a visible tree at a purposeful site position.
    ob.location=(247,-240+i*19,0);templates.append(ob)

def palm(x,y,scale=1,context=False):
    base=rng.choice(templates);ob=bpy.data.objects.new('Coconut_palm',base.data)
    (env if context else plants).objects.link(ob);ob.location=(x,y,.22)
    f=scale*rng.uniform(.82,1.15);ob.scale=(f,f,f*rng.uniform(.95,1.1));ob.rotation_euler.z=rng.uniform(0,math.tau)
    return ob

def ellipsoid(mesh,c,r,material,n=10,m=6):
    for j in range(m):
        a=-math.pi/2+math.pi*j/m;b=-math.pi/2+math.pi*(j+1)/m
        for i in range(n):
            t=i*math.tau/n;u=(i+1)*math.tau/n
            mesh.face([(c[0]+r[0]*math.cos(v)*math.cos(w),c[1]+r[1]*math.cos(v)*math.sin(w),c[2]+r[2]*math.sin(v)) for v,w in [(a,t),(a,u),(b,u),(b,t)]],material,True)

shrubmesh=Mesh()
for i in range(13):
    a=i*2.4;rad=rng.uniform(0,.8)
    ellipsoid(shrubmesh,(rad*math.cos(a),rad*math.sin(a),rng.uniform(.55,1.0)),(.62,.58,.49),['leaf','leaf_light','leaf_deep'][i%3])
shrub=shrubmesh.object('Shrub_prototype',plants);shrub.location=(-189,-72,.2)
def bush(x,y,s=1,flower=False):
    ob=bpy.data.objects.new('Landscape_shrub',shrub.data);plants.objects.link(ob);ob.location=(x,y,.18);ob.scale=(s,s,s*.75);ob.rotation_euler.z=rng.random()*6.28

# Formal avenues, roadside coconut allees and dune planting.
for yy in range(-269,270,17):
    palm(-198,yy,.9);palm(246,yy,1.0)
for xx in range(-184,230,18):
    for yy in (-270,270):palm(xx,yy,.88)
for xx in range(-183,184,18):
    if abs(xx+3)>58:
        for yy in (-17,17):palm(xx,yy,.67)
for i in range(52):
    yy=-285+i*11+rng.uniform(-3,3);palm(270+rng.uniform(-6,8),yy,.91)
for j in range(28):
    a=j*math.tau/28;x=-3+56.5*math.cos(a);y=56.5*math.sin(a)
    if abs(y)>13:palm(x,y,.82)

# Gardens inside the crescents: leave pool water, decks and paths clear.
for sp,ps in zip(PARAMS['towers'],pool_specs):
    cx,cy=sp['cx'],sp['cy'];px,py,prx,pry,sea=ps;placed=0;tries=0
    while placed<88 and tries<4000:
        tries+=1;x=cx+rng.uniform(-45,73);y=cy+rng.uniform(-69,69)
        er=((x-cx-16)/61)**2+((y-cy)/68)**2
        poold=((x-px)/(prx+11))**2+((y-py)/(pry+11))**2
        if er>1 or poold<1 or (abs(y-cy)<5 and x<px):continue
        u=(y-cy)/sp['ry'];wall_x=planpoint(sp,u)[0]
        if x<wall_x+20:continue
        if sp['id']=='B_Sea_North' and 194<x<231 and 98<y<212:continue
        if sp['id']=='D_Sea_South' and x>201 and y<-193:continue
        palm(x,y,rng.uniform(.88,1.22));placed+=1
    for i in range(65):
        a=i*math.tau/65;x=cx+16+67*math.cos(a);y=cy+75*math.sin(a)
        # The path border planting stops before reaching the tower shell.
        t=math.atan2((y-cy)/sp['ry'],-(x-cx)/sp['rx'])
        rr=((x-cx)/sp['rx'])**2+((y-cy)/sp['ry'])**2
        if abs(t)<2.12 and .68<rr<1.45:continue
        bush(x,y,rng.uniform(.6,1.2))
for xx,yy in shop_positions:
    for sg in(-1,1):
        for oo in(-7.5,7.5):bush(xx+oo,yy+sg*15,.65)

# Planted beds and benches around the circular square.
misc=Mesh()
for j in range(18):
    a=j*math.tau/18;x=-3+59*math.cos(a);y=59*math.sin(a)
    if abs(y)<19:continue
    misc.box((x,y,.9),(3.8,.65,.25),'wood',a+math.pi/2)
    for q in(-1.35,1.35):
        misc.box((x-q*math.sin(a),y+q*math.cos(a),.55),(.18,.5,.65),'metal',a)

# Pool parasols and tropical beach umbrellas: reusable detailed radial canvas.
umb=Mesh();umb.beam((0,0,0),(0,0,3.15),.05,'wood',8)
for i in range(12):
    a=i*math.tau/12;b=(i+1)*math.tau/12;m=(a+b)/2
    p=(2*math.cos(a),2*math.sin(a),2.65);q=(2*math.cos(b),2*math.sin(b),2.65)
    ridge=(1.02*math.cos(m),1.02*math.sin(m),3.15)
    umb.face([(0,0,3.42),p,ridge],'fabric');umb.face([p,q,ridge],'fabric');umb.face([q,(0,0,3.42),ridge],'fabric')
    umb.beam((0,0,3.24),p,.018,'wood',4)
template=umb.object('Parasol',amen);template.location=(282,-263,.1)
for ps in pool_specs:
    cx,cy,rx,ry,sea=ps
    for i in range(9 if sea else 6):
        a=i*math.tau/(9 if sea else 6)
        ob=bpy.data.objects.new('Pool_parasol',template.data);amen.objects.link(ob)
        ob.location=(cx+(rx+12)*math.cos(a),cy+(ry+12)*math.sin(a),.25)
for yy in range(-248,249,16):
    for xx in(288,302):
        ob=bpy.data.objects.new('Beach_parasol',template.data);amen.objects.link(ob);ob.location=(xx,yy,.07)
        for d in(-1.25,1.25):misc.box((xx+d,yy-1.5,.43),(.9,2.1,.23),'fabric')

# Tensile white sails next to the smaller courtyard pools, as seen in actual photos.
for sp in [PARAMS['towers'][0],PARAMS['towers'][2]]:
    cx=sp['cx']+10;cy=sp['cy']-29
    poles=[(cx-8,cy-5,5.8),(cx+9,cy-7,2.7),(cx+6,cy+6,6.5),(cx-8,cy+7,2.5)]
    for p in poles:misc.beam((p[0],p[1],.3),p,.09,'ivory',8)
    a,b,c,d=[Vector(p) for p in poles]
    for i in range(18):
        for j in range(18):
            pts=[]
            for u,v in((i/18,j/18),((i+1)/18,j/18),((i+1)/18,(j+1)/18),(i/18,(j+1)/18)):
                q=a*(1-u)*(1-v)+b*u*(1-v)+c*u*v+d*(1-u)*v;q.z-=.8*math.sin(math.pi*u)*math.sin(math.pi*v);pts.append(q)
            misc.face(pts,'fabric',True)
# Slim light standards establish human scale.
for xx in range(-185,206,23):
    for yy in(-11,11):
        if xx*xx+yy*yy<56*56:continue
        misc.beam((xx,yy,.25),(xx,yy,5.1),.065,'metal',6)
        misc.box((xx,yy,5.17),(1,.32,.12),'ivory')
misc.object('Parasols_benches_pavilions_and_lighting',amen)

# Render-only surroundings; independent collection excluded from the core export.
context=Mesh();context.box((-5500,0,-1.6),(10500,22000,2),'grass')
context.box((20,-1025,-1.5),(490,1400,2),'grass');context.box((20,1025,-1.5),(490,1400,2),'grass')
context.box((284,0,-.46),(80,22000,.7),'sand')
context.box((6300,0,-.57),(11960,22000,.4),'ocean')
# Thin broken wave crests at the shoreline, original mesh ripples.
for line in range(3):
    pts=[(318+line*5+1.5*math.sin(yy*.037+line),yy) for yy in range(-1650,1650,3)]
    context.ribbon(pts,.28+line*.12,-.35+line*.008,'foam')
context.object('Beach_sea_and_context_ground',env)
for i in range(220):
    x=rng.uniform(-370,-264);y=rng.uniform(-420,420);palm(x,y,rng.uniform(.8,1.2),True)
for i in range(130):
    x=rng.uniform(-196,245);y=rng.choice([-1,1])*rng.uniform(307,440);palm(x,y,rng.uniform(.8,1.3),True)
save_stage('landscape_and_beach')
