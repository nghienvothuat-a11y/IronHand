"""Four horseshoe wings, stepped floor plates and individual facade bays."""
for spec in PARAMS['towers']:
    cx,cy,rx,ry,nf=[spec[k] for k in ('cx','cy','rx','ry','floors')]
    c=collection('EMP_10_'+spec['id']); slabs=Mesh();wall=Mesh();frame=Mesh();rails=Mesh();roof=Mesh();details=Mesh()
    maxa=math.radians(119); bay_step=maxa/38
    def halfangle(k):
        # Three low levels run to the tips; the stepped ends climb to the crown.
        frac=max(0,(k-3)/(nf-3))
        return maxa-(maxa-.47)*frac
    # Transparent-looking lobby shell, no rooms or interior geometry.
    arc_strip(slabs,cx,cy,rx,ry,12.5,-maxa,maxa,1.05,.65,n=148)
    arc_strip(slabs,cx,cy,rx,ry,11.3,-maxa,maxa,5.2,.38,n=148)
    for side in (-1,1):
        for b in range(80):
            t=-maxa+2*maxa*b/80;u=-maxa+2*maxa*(b+1)/80
            rxx,ryy=rx+side*8.8,ry+side*8.8
            wall.face([arcpt(cx,cy,rxx,ryy,t,1.1),arcpt(cx,cy,rxx,ryy,u,1.1),arcpt(cx,cy,rxx,ryy,u,5),arcpt(cx,cy,rxx,ryy,t,5)],'glass')
            p=arcpt(cx,cy,rxx,ryy,t,3)
            frame.box(p,(.28,.35,4),'ivory',-t)
    for k in range(nf):
        z=5.2+k*3.05; a=halfangle(k); nexta=halfangle(k+1)
        arc_strip(slabs,cx,cy,rx,ry,11.6,-a,a,z,.26,n=144)
        # End terraces use real exposed slabs instead of a smooth sloped solid.
        if k>=3:
            for sign in (-1,1):
                aa,bb=sorted((sign*nexta,sign*a))
                arc_strip(roof,cx,cy,rx,ry,10.9,aa,bb,z+3.065,.09,'pale',n=5)
                for edge in (-1,1):
                    pts=[arcpt(cx,cy,rx+edge*11.2,ry+edge*11.2,aa+(bb-aa)*j/5,z+4.1) for j in range(6)]
                    for j in range(5):rails.beam(pts[j],pts[j+1],.055,'ivory')
        bays=max(12,round(2*a/bay_step))
        for j in range(bays):
            t=-a+2*a*j/bays;u=-a+2*a*(j+1)/bays;mid=(t+u)/2
            for side in (-1,1):
                # Recessed glazed doors, opaque fins, projecting balcony slabs.
                rxx,ryy=rx+side*8.7,ry+side*8.7
                pane='glass' if rng.random()>.19 else ('glass_light' if rng.random()>.45 else 'curtain')
                wall.face([arcpt(cx,cy,rxx,ryy,t,z+.26),arcpt(cx,cy,rxx,ryy,u,z+.26),arcpt(cx,cy,rxx,ryy,u,z+2.86),arcpt(cx,cy,rxx,ryy,t,z+2.86)],pane)
                for v in (t,mid):
                    p0=arcpt(cx,cy,rxx,ryy,v,z+.28);p1=arcpt(cx,cy,rxx,ryy,v,z+2.9)
                    frame.beam(p0,p1,.075 if v==t else .038,'metal',4)
                fin=arcpt(cx,cy,rx+side*9.8,ry+side*9.8,t,z+1.6)
                frame.box(fin,(2.5,.18,2.85),'ivory',-t)
                # Segmented balustrades, avoid a visually opaque continuous band.
                rr,rry=rx+side*11.35,ry+side*11.35
                p0=arcpt(cx,cy,rr,rry,t+.003,z+.40);p1=arcpt(cx,cy,rr,rry,u-.003,z+.40)
                p2=(p1[0],p1[1],z+1.37);p3=(p0[0],p0[1],z+1.37)
                rails.face([p0,p1,p2,p3],'rail')
                rails.beam(p3,p2,.05,'ivory',5)
                rails.beam(p0,p3,.045,'metal',4)
                # White bay aprons alternate across the convex outer elevation.
                if side==1 and (j+k//2)%4==0:
                    wall.face([arcpt(cx,cy,rr,rry,t,z+.30),arcpt(cx,cy,rr,rry,u,z+.30),arcpt(cx,cy,rr,rry,u,z+1.13),arcpt(cx,cy,rr,rry,t,z+1.13)],'ivory')
        # Closed end walls and paired terrace guard rails.
        for sign in (-1,1):
            t=sign*a
            wall.face([arcpt(cx,cy,rx-8.7,ry-8.7,t,z+.25),arcpt(cx,cy,rx+8.7,ry+8.7,t,z+.25),arcpt(cx,cy,rx+8.7,ry+8.7,t,z+2.95),arcpt(cx,cy,rx-8.7,ry-8.7,t,z+2.95)],'ivory')
            p0=arcpt(cx,cy,rx-11.4,ry-11.4,t,z+1.4);p1=arcpt(cx,cy,rx+11.4,ry+11.4,t,z+1.4)
            rails.beam(p0,p1,.065,'ivory')
        # Service-window rhythm on the convex west apex: recognizable white grid.
        for j in range(-5,6):
            t=j*.037
            p=arcpt(cx,cy,rx+11.4,ry+11.4,t,z+1.5)
            frame.box(p,(.23,.25,3.0),'ivory',-t)
    crown=5.2+nf*3.05; a=halfangle(nf)
    arc_strip(slabs,cx,cy,rx,ry,11.7,-a,a,crown,.35,n=60)
    arc_strip(roof,cx,cy,rx,ry,10.9,-a,a,crown+.04,0,'roof',n=60)
    for side in (-1,1):
        arc_strip(roof,cx,cy,rx+side*10.8,ry+side*10.8,.35,-a,a,crown+.65,.65,'ivory',n=60)
    for j in range(7):
        t=-a*.8+j*a*1.6/6; p=arcpt(cx,cy,rx,ry,t,crown+1.3)
        roof.box(p,(4,2.5,2),'ivory',-t)
        roof.box((p[0],p[1],crown+2.34),(3.4,1.9,.1),'metal',-t)
        for q in range(7):
            pos=(p[0]+(q-3)*.42*math.cos(t),p[1]-(q-3)*.42*math.sin(t),crown+2.42)
            roof.box(pos,(.06,1.8,.04),'black',-t)
    # Ground lobby canopy with tapered supports on inward-facing apex.
    details.box((cx-rx+24,cy,5),(19,27,.45),'ivory')
    for yy in (cy-12,cy+12):
        details.beam((cx-rx+27,yy,.8),(cx-rx+32,yy,4.8),.28,'ivory',10)
    for mesh,label in [(slabs,'Floor_plates'),(wall,'Glazing_and_spandrels'),(frame,'Fins_and_mullions'),(rails,'Balustrades'),(roof,'Roof_and_terraces'),(details,'Entrance')]:
        mesh.object(spec['id']+'_'+label,c)
    print('BUILT',spec['id'],'crown_height',round(crown,2))
save_stage('tower_exteriors')
