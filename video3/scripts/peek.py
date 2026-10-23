"""peek.py t1 t2 ... -> work/peek/<t>.jpg  full-res app crop (src y 105..893) with a labelled 100 px grid in SOURCE coordinates"""
import sys, subprocess, cv2, os
os.makedirs('peek', exist_ok=True)
for t in sys.argv[1:]:
    subprocess.check_call(['ffmpeg','-v','error','-y','-ss',t,'-i','../source.mp4','-frames:v','1','peek/x.png'])
    im=cv2.imread('peek/x.png')[105:893].copy(); im=cv2.convertScaleAbs(im,alpha=1.8,beta=10)
    for gx in range(0,1080,100): cv2.line(im,(gx,0),(gx,788),(0,120,255),1); cv2.putText(im,str(gx),(gx+2,11),0,0.4,(0,255,255),1)
    for gy in range(105,893,100):
        y=gy-105; cv2.line(im,(0,y),(1080,y),(0,120,255),1); cv2.putText(im,str(gy),(2,y+11),0,0.4,(0,255,255),1)
    cv2.putText(im,t+'s',(950,60),0,1.0,(0,255,0),2); cv2.imwrite(f'peek/{t}.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,80])
