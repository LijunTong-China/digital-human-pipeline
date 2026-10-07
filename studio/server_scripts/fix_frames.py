import cv2, numpy as np, os
VID='/root/autodl-tmp/echomimic_v2/outputs/pretrained_weights-itermotion_module-seed3407/ref.char_ref1.png/01/char_ref1-a-v2_p00_short.wav-i0_sig.mp4'
REF='/root/autodl-tmp/echomimic_v2/assets/ref/char_ref1.png'
OUT='/root/autodl-tmp/fix_out'; os.makedirs(OUT, exist_ok=True)
LO,HI=48,96  # 2s @24fps
ref=cv2.imread(REF); 
# head crop of ref (tune to actual head position)
hx,hy,hw,hh=240,30,300,320
ref_head=ref[hy:hy+hh, hx:hx+hw]
ref_gray=cv2.cvtColor(ref_head,cv2.COLOR_BGR2GRAY)
cap=cv2.VideoCapture(VID); fps=cap.get(cv2.CAP_PROP_FPS)
frames={}
i=0
while True:
    ok,fr=cap.read()
    if not ok: break
    frames[i]=fr; i+=1
cap.release()
print('frames',len(frames))
# feathered elliptical mask over hair/forehead/glasses zone (ref_head coords)
mask=np.zeros((hh,hw),np.float32)
cv2.ellipse(mask,(150,120),(125,105),0,0,360,1.0,-1)
mask=cv2.GaussianBlur(mask,(51,51),0)
warp_mode=cv2.MOTION_AFFINE
crit=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,80,1e-6)
vw=cv2.VideoWriter(OUT+'/cmp.mp4',cv2.VideoWriter_fourcc(*'mp4v'),fps,(768*2,768))
fixed=0
for idx in range(LO,HI):
    fr=frames[idx]
    fr_gray=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
    warp=np.eye(2,3,dtype=np.float32)
    try:
        cc, warp=cv2.findTransformECC(ref_gray,fr_gray[hy:hy+hh,hx:hx+hw],warp,warp_mode,crit,None,5)
    except cv2.error as e:
        print('ecc fail',idx); vw.write(np.hstack([fr,fr])); continue
    warped_head=cv2.warpAffine(ref_head,warp,(hw,hh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    warped_m=cv2.warpAffine(mask,warp,(hw,hh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    roi=fr[hy:hy+hh,hx:hx+hw]
    m3=warped_m[...,None]
    blend=(warped_head*m3+roi*(1-m3)).astype(np.uint8)
    fr2=fr.copy(); fr2[hy:hy+hh,hx:hx+hw]=blend
    fixed+=1
    vw.write(np.hstack([fr,fr2]))
vw.release()
print('fixed frames',fixed)
os.system(f'ffmpeg -y -i {OUT}/cmp.mp4 -pix_fmt yuv420p {OUT}/cmp_final.mp4 -loglevel error')
print('DONE')
