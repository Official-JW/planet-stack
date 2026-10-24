import json,struct,numpy as np
def load(p):
    b=open(p,'rb').read();n=struct.unpack('<I',b[12:16])[0];j=json.loads(b[20:20+n]);bin_=bytearray(b[20+n+8:]);return j,bin_
CT={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8,5122:np.int16,5120:np.int8}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def acc(j,B,i):
    a=j['accessors'][i];bv=j['bufferViews'][a['bufferView']];dt=np.dtype(CT[a['componentType']]);nc=NC[a['type']]
    st=bv.get('byteStride',dt.itemsize*nc);off=bv.get('byteOffset',0)+a.get('byteOffset',0)
    arr=np.ndarray((a['count'],nc),dtype=dt,buffer=B,offset=off,strides=(st,dt.itemsize))
    return arr
def save(p,j,B):
    js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
    B=bytes(B);B+=b'\0'*((4-len(B)%4)%4);j['buffers'][0]['byteLength']=len(B)
    js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
    out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(B))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(B),0x004E4942)+B
    open(p,'wb').write(out)
