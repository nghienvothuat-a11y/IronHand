"""Photo-guided v2: fixed bay grid, tight rounded U plan, sawtooth rear."""
M['trim_blue']=mat('Facade_blue_reveal',(.035,.075,.155),.48)
M['trim_coral']=mat('Facade_terracotta_reveal',(.31,.060,.027),.6)
for spec in PARAMS['towers']:
    cx,cy,rx,ry,nf=[spec[k] for k in ('cx','cy','rx','ry','floors')]
    c=collection('EMP_10_'+spec['id']);slabs=Mesh();wall=Mesh();frame=Mesh();rails=Mesh();roof=Mesh();details=Mesh()
    maxa=math.radians(119);step=maxa/40
    trim='trim_coral' if spec['id'].startswith('A_') else ('trim_blue' if spec['id'].startswith('B_') else 'soffit')
    def nb(k,sg=1):
        crown_bays=spec['crown_negative' if sg<0 else 'crown_positive']
        return max(crown_bays,40-round((40-crown_bays)*max(0,k-2)/max(1,nf-2)))
    def ap(r,t,z):return arcpt(cx,cy,rx+r,ry+r,t,z)
    arc_strip(slabs,cx,cy,rx,ry,11.6,-maxa,maxa,1.0,.6,n=160)
    arc_strip(slabs,cx,cy,rx,ry,11.5,-maxa,maxa,5.2,.4,n=160)
    for j in range(-40,40):
        t=j*step;u=(j+1)*step
        for side in(-1,1):
            pts=[ap(side*8.8,t,1),ap(side*8.8,u,1),ap(side*8.8,u,5),ap(side*8.8,t,5)]
            wall.face(pts if side<0 else list(reversed(pts)),'glass')
            frame.box(ap(side*9,t,3),(.5,.45,4.1),'ivory',facade_angle(rx,ry,t,cx,cy))
    for k in range(nf):
        z=5.2+k*3.05;left=nb(k,-1);right=nb(k,1);a=right*step
        arc_strip(slabs,cx,cy,rx,ry,11.45,-left*step,right*step,z,.26,n=(left+right)*2)
        for j in range(-left,right):
            t=j*step;u=(j+1)*step;mid=(t+u)/2
            pane='glass' if rng.random()>.28 else ('curtain' if rng.random()>.55 else 'glass_light')
            wall.face([ap(-8.45,t+.002,z+.30),ap(-8.45,u-.002,z+.30),ap(-8.45,u-.002,z+2.86),ap(-8.45,t+.002,z+2.86)],pane)
            frame.box(ap(-9.75,t,z+1.60),(2.9,.29,2.94),'ivory',facade_angle(rx,ry,t,cx,cy))
            frame.beam(ap(-8.42,mid,z+.32),ap(-8.42,mid,z+2.87),.045,'metal',4)
            frame.beam(ap(-8.42,t,z+2.88),ap(-8.42,u,z+2.88),.06,'ivory',4)
            p0=ap(-11.15,t+.005,z+.36);p1=ap(-11.15,u-.005,z+.36)
            p2=(p1[0],p1[1],z+1.31);p3=(p0[0],p0[1],z+1.31)
            rails.face([p0,p1,p2,p3],'rail');rails.beam(p3,p2,.042,'metal',5)
            p0=ap(-11.48,t,z+.04);p1=ap(-11.48,u,z+.04)
            wall.face([p0,p1,(p1[0],p1[1],z+.25),(p0[0],p0[1],z+.25)],trim)
            # Rounded rear core: narrow punched windows and blank horizontal spandrels.
            if -9 <= j < 9:
                q0=ap(11.51,t,z+.28);q1=ap(11.51,u,z+.28)
                wall.face([q1,q0,(q0[0],q0[1],z+2.95),(q1[0],q1[1],z+2.95)],'ivory')
                for sub in range(3):
                    ta=t+step*(.11+sub*.29);tb=ta+step*.125
                    p0=ap(11.55,ta,z+.78);p1=ap(11.55,tb,z+.78)
                    wall.face([p1,p0,(p0[0],p0[1],z+2.54),(p1[0],p1[1],z+2.54)],'glass')
            elif j in(-11,-10,9,10):
                p0=ap(11.52,t,z+.25);p1=ap(11.52,u,z+.25)
                wall.face([p1,p0,(p0[0],p0[1],z+2.97),(p1[0],p1[1],z+2.97)],'black' if j in(-10,9) else 'ivory')
                if j in(-10,9):
                    frame.beam(ap(11.55,t,z+1.5),ap(11.55,u,z+1.5),.055,'metal',4)
            else:
                t0=t+.002;t1=t+.83*step;t2=u-.002
                a0=ap(11.5,t0,z+.3);a1=ap(12.4,t1,z+.3);a2=ap(10.6,t2,z+.3)
                b0=(a0[0],a0[1],z+2.89);b1=(a1[0],a1[1],z+2.89);b2=(a2[0],a2[1],z+2.89)
                wall.face([a1,a0,b0,b1],'ivory');wall.face([a2,a1,b1,b2],'ivory');frame.beam(a2,b2,.065,'ivory',4)
                c0=Vector(a2).lerp(Vector(a1),.16);c1=Vector(a2).lerp(Vector(a1),.88)
                # Recessed side window framed by substantial white spandrels.
                c0.z=z+.77;c1.z=z+.77;d0=c0.copy();d1=c1.copy();d0.z=z+2.46;d1.z=z+2.46
                n=(Vector(a1)-Vector(a2)).cross(Vector((0,0,1))).normalized()*.008
                wall.face([c0+n,c1+n,d1+n,d0+n],pane)
                for q0,q1 in((a0,a1),(a1,a2)):
                    wall.face([(q1[0],q1[1],z+.035),(q0[0],q0[1],z+.035),(q0[0],q0[1],z+.23),(q1[0],q1[1],z+.23)],trim)
                    slabs.face([(q0[0],q0[1],z),(q1[0],q1[1],z),ap(8.8,t2,z),ap(8.8,t0,z)],'ivory')
        for sg in(-1,1):
            bays=nb(k,sg);nextb=nb(k+1,sg);a=bays*step;t=sg*a
            wall.face([ap(-8.8,t,z+.25),ap(8.8,t,z+.25),ap(8.8,t,z+2.95),ap(-8.8,t,z+2.95)],'ivory')
            rails.beam(ap(-11.4,t,z+1.30),ap(11.4,t,z+1.30),.05,'metal',6)
            q0=ap(-6.8,t+sg*.001,z+1.25);q1=ap(-1.2,t+sg*.001,z+1.25)
            wall.face([q0,q1,(q1[0],q1[1],z+2.25),(q0[0],q0[1],z+2.25)],'glass')
            if nextb<bays:
                ta,tb=sorted((sg*nextb*step,sg*a))
                arc_strip(roof,cx,cy,rx,ry,10.8,ta,tb,z+3.055,.1,'pale',n=max(6,(bays-nextb)*4))
                for q in range(19):
                    d=-10+q*20/18;roof.beam(ap(d,ta,z+3.58),ap(d,tb,z+3.58),.064,'ivory',4)
                for tt in(ta,tb):
                    roof.beam(ap(-10,tt,z+3.58),ap(10,tt,z+3.58),.1,'ivory',4)
                    for d in(-10,10):roof.beam(ap(d,tt,z+3.07),ap(d,tt,z+3.6),.05,'ivory',4)
    crown=5.2+nf*3.05;al=nb(nf,-1)*step;ar=nb(nf,1)*step;a=(al+ar)/2
    arc_strip(slabs,cx,cy,rx,ry,11.5,-al,ar,crown,.36,n=90)
    arc_strip(roof,cx,cy,rx,ry,10.7,-al,ar,crown+.045,0,'roof',n=90)
    for side in(-1,1):arc_strip(roof,cx,cy,rx+side*10.9,ry+side*10.9,.22,-al,ar,crown+.7,.7,'ivory',n=90)
    for j in range(9 if nf>15 else 14):
        t=-a*.9+j*a*1.8/(8 if nf>15 else 13);pos=ap(0,t,crown+.8);ang=facade_angle(rx,ry,t,cx,cy)
        roof.box(pos,(2.6,1.5,1.4),'ivory',ang);roof.box((pos[0],pos[1],crown+1.53),(2.4,1.35,.08),'metal',ang)
    details.box((cx-rx+21,cy,4.7),(20,19,.45),'ivory')
    for yy in(cy-8,cy+8):details.beam((cx-rx+28,yy,.8),(cx-rx+28,yy,4.5),.22,'ivory',8)
    for sg in(-1,1):
        t=sg*maxa;pos=ap(0,t,4);ang=facade_angle(rx,ry,t,cx,cy)
        details.box((pos[0]+7,pos[1],5.8),(18,20,.35),'ivory',ang)
        details.box((pos[0]+7,pos[1],9.7),(18,20,.35),'ivory',ang)
        details.box((pos[0]+7,pos[1],7.75),(15.9,18.3,3.45),'glass_light',ang)
        for off in(-7.5,7.5):
            q=ap(off,t,2.75);details.beam((q[0]+7,q[1],.6),(q[0]+7,q[1],5.75),.28,'ivory',8)
    for mesh,label in[(slabs,'Floor_plates'),(wall,'Glazing_and_spandrels'),(frame,'Fins_and_mullions'),(rails,'Balustrades'),(roof,'Roof_and_terraces'),(details,'Entrance')]:mesh.object(spec['id']+'_'+label,c)
    print('BUILT_PHOTO_V2',spec['id'],nf,crown)
# Separate source for the outward-curving low pavilion.
exec(compile((ROOT/'source'/'stages'/'12_pavilion.py').read_text(),'12_pavilion.py','exec'))
save_stage('four_individual_towers_outward_pavilion')
