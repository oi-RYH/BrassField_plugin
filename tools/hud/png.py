import zlib,struct
def read(path):
    data=path if isinstance(path,(bytes,bytearray)) else open(path,'rb').read(); assert data[:8]==b'\x89PNG\r\n\x1a\n'
    i=8; idat=b''; plte=None; trns=None
    while i<len(data):
        n=struct.unpack('>I',data[i:i+4])[0]; t=data[i+4:i+8]; d=data[i+8:i+8+n]; i+=12+n
        if t==b'IHDR': w,h,bd,ct,_,_,il=struct.unpack('>IIBBBBB',d)
        elif t==b'PLTE': plte=[tuple(d[j:j+3]) for j in range(0,len(d),3)]
        elif t==b'tRNS': trns=d
        elif t==b'IDAT': idat+=d
    assert il==0 and (bd==8 or (bd<8 and ct in (0,3))), (bd,il)
    ch={6:4,2:3,3:1,0:1,4:2}[ct]; raw=zlib.decompress(idat); px=[]; p=0
    if bd<8:  # 팔레트·회색 1/2/4비트: 한 줄을 바이트 단위로 필터를 풀고 비트를 나눈다
        stride=(w*bd+7)//8; prev=bytearray(stride)
        for y in range(h):
            f=raw[p]; p+=1; line=bytearray(raw[p:p+stride]); p+=stride
            for x in range(stride):
                a=line[x-1] if x>=1 else 0; b=prev[x]; c=prev[x-1] if x>=1 else 0
                if f==1: line[x]=(line[x]+a)&255
                elif f==2: line[x]=(line[x]+b)&255
                elif f==3: line[x]=(line[x]+((a+b)>>1))&255
                elif f==4:
                    pa,pb,pc=abs(b-c),abs(a-c),abs(a+b-2*c)
                    pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c); line[x]=(line[x]+pr)&255
            prev=line; row=[]; per=8//bd; mask=(1<<bd)-1
            for x in range(w):
                v=(line[x//per]>>(8-bd*(x%per+1)))&mask
                if ct==3: row.append(plte[v]+((trns[v] if trns and v<len(trns) else 255),))
                else: g=v*255//mask; row.append((g,g,g,255))
            px.append(row)
        return px
    stride=w*ch; prev=bytearray(stride)
    for y in range(h):
        f=raw[p]; p+=1; line=bytearray(raw[p:p+stride]); p+=stride
        for x in range(stride):
            a=line[x-ch] if x>=ch else 0; b=prev[x]; c=prev[x-ch] if x>=ch else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+((a+b)>>1))&255
            elif f==4:
                pa,pb,pc=abs(b-c),abs(a-c),abs(a+b-2*c)
                pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c); line[x]=(line[x]+pr)&255
        prev=line; row=[]
        for x in range(w):
            s=line[x*ch:(x+1)*ch]
            if ct==6: row.append(tuple(s))
            elif ct==2: row.append((s[0],s[1],s[2],255))
            elif ct==3:
                idx=s[0]; a=trns[idx] if trns and idx<len(trns) else 255; row.append(plte[idx]+(a,))
            elif ct==0: row.append((s[0],s[0],s[0],255))
            elif ct==4: row.append((s[0],s[0],s[0],s[1]))
        px.append(row)
    return px
def write(path,px):
    h=len(px); w=len(px[0])
    raw=b''.join(b'\x00'+b''.join(bytes(c) for c in row) for row in px)
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))
def crop(px,x,y,w,h): return [row[x:x+w] for row in px[y:y+h]]
def scale(px,k): return [[c for c in row for _ in range(k)] for row in px for _ in range(k)]
def blank(w,h): return [[(0,0,0,0)]*w for _ in range(h)]
def paste(dst,src,x,y):
    for j,row in enumerate(src):
        for i,c in enumerate(row):
            if 0<=y+j<len(dst) and 0<=x+i<len(dst[0]): dst[y+j][x+i]=c
