import tkinter as tk
import tkinter.font as tkfont
import threading
import psutil 
import datetime
import time
import math
# import pystray
# from PIL import Image, ImageDraw
import os

try:
    import pystray
    from PIL import Image,ImageDraw
    TRAY_AVAILABLE=True
except ImportError:
    TRAY_AVAILABLE=False
    print("⚠  pystray/pillow not found. Run: pip install pystray pillow")

BG    = "#020912"
BG2   = "#040f1e"
BORDER= "#0a2a45"
CYAN  = "#7ec8e3"
BLUE  = "#00ccff"
GREEN = "#00ff88"
DIM   = "#1a3a55"
DIM2  = "#0a2040"
WHITE = "#d0eeff"

W_GUI= 540
H_GUI= 440
MIN_W= 400
MIN_H= 60
EDGE = 4
CORNER=10


def _hex_points(cx, cy,r):
    pts=[]
    for i in range(6):
        a=(i/6)* math.pi*2-math.pi/6
        pts.append(cx+math.cos(a)*r)
        pts.append(cy+math.sin(a)*r)
    return pts

class JarvisGUI:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.geometry(f"{W_GUI}x{H_GUI}+400+200")
        self.root.configure(bg=BG)
        self.root.resizable(False,False)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)

        self._drag_x=self._drag_y=0
        self.root.bind("<ButtonPress-1>",self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<Map>",self._on_map)

        self.status= "SLEEPING"
        self.start_ts  = time.time()
        self._angle=0.0
        self._wave_t=0.0
        self._maximized=False
        self._restore_geom=None
        self._size=(0,0)
        self._rs=None
        self._bar_max=155
        self._stat_vals={"cpu":0,"ram":0,"bat":0}
        self._charging=False
        self._chat_fs=9

        self._build_background_canvas()
        self._build_ui()
        self._build_grips()
        self._relayout(W_GUI,H_GUI)
        self.root.bind("<Configure>",self._on_configure)
        self._tick_animation()
        self._tick_stats()
        self._tick_clock()

    def _start_drag(self,e):
        self._drag_x=e.x_root-self.root.winfo_x()
        self._drag_y=e.y_root-self.root.winfo_y()

    def _on_drag(self,e):
        if self._maximized:
            return
        self.root.geometry(f"+{e.x_root-self._drag_x}+{e.y_root-self._drag_y}")

    def _build_background_canvas(self):
        self.bg=tk.Canvas(
            self.root,width=W_GUI,height=H_GUI,
            bg=BG,highlightthickness=0
        )
        self.bg.place(x=0,y=0)

    def _build_ui(self):

        self._hdr=tk.Frame(self.root,bg=BG2,height=44)
        self._hdr.place(x=0,y=0,width=W_GUI)
        self._hdr.bind("<Double-Button-1>",lambda e:self.toggle_mode())

        tk.Label(self._hdr, text="J.A.R.V.I.S",
                 font=("Courier New", 14,"bold"),
                bg=BG2, fg= CYAN).place(x=14,y=5)
        tk.Label(self._hdr, text="PERSONAL AI SYSTEM",
                 font=("Courier New",7),
                 bg=BG2,fg=DIM).place(x=14,y=28)
        
        self._pill_canvas=tk.Canvas(
            self.root, width=136,height=26,
            bg=BG2,highlightthickness=0
        )
        self._draw_pill()

        self._sep0=tk.Frame(self.root,bg=BORDER,height=1)
        self._sep0.place(x=0,y=44,width=W_GUI)

        self._cpu_var=tk.StringVar(value="--")
        self._ram_var=tk.StringVar(value="--")
        self._bat_var=tk.StringVar(value="--")
        self._stat_bars={}
        self._bar_bgs=[]
        self._stats_bg=tk.Frame(self.root, bg=BORDER)
        self._stats_bg.place(x=0,y=45,width=W_GUI,height=64)

        stat_defs=[
            ("CPU LOAD", self._cpu_var,BLUE, "cpu"),
            ("MEMORY", self._ram_var,BLUE, "ram"),
            ("BATTERY", self._bat_var,GREEN, "bat"),
        ]
        self._stat_frames=[]
        for i , (label, var,color,key) in enumerate(stat_defs):
            fx=i*180
            f=tk.Frame(self._stats_bg,bg=BG,width=179,height=64)
            f.place(x=fx+i,y=0)
            self._stat_frames.append(f)

            tk.Label(f,text=label, font=("Courier New",7),
                     bg=BG,fg=DIM).place(x=10,y=6)
            tk.Label(f,textvariable=var,
                     font=("Courier New", 19,"bold"),
                     bg=BG,fg=CYAN).place(x=10,y=18)
            
            bar_bg=tk.Frame(f,bg=DIM2,width=155,height=2)
            bar_bg.place(x=10,y=56)
            self._bar_bgs.append(bar_bg)
            bar=tk.Frame(f,bg=color,width=0,height=2)
            bar.place(x=10,y=56)
            self._stat_bars[key]=(bar,color)
        self._sep1=tk.Frame(self.root,bg=BORDER,height=1)
        self._sep1.place(x=0,y=109,width=W_GUI)
        self._chat_frame=tk.Frame(self.root,bg=BG)
        self._chat_frame.place(x=0,y=110,width=W_GUI,height=152)

        self._chat=tk.Text(
            self._chat_frame,
            bg=BG,fg=CYAN,
            font=("Courier New",9),
            bd=0,highlightthickness=0,
            insertbackground=CYAN,
            state="disabled",
            wrap="word",
            padx=14,pady=8,        
            )
        self._chat.place(x=0,y=0,relwidth=1,relheight=1)

        self._chat.tag_config("pre_you",   foreground=BLUE)
        self._chat.tag_config("txt_you",   foreground="#2a5a7a")
        self._chat.tag_config("pre_jarvis",foreground=GREEN)
        self._chat.tag_config("txt_jarvis",foreground=CYAN)
        self._chat.tag_config("sys",     foreground=DIM,
                              font=("Courier New",8))
        
        self._sep2=tk.Frame(self.root,bg=BORDER,height=1)
        self._sep2.place(x=0,y=262,width=W_GUI)

        self._wave_bg=tk.Frame(self.root,bg=BG,height=38)
        self._wave_bg.place(x=0,y=263,width=W_GUI)
        self._wave_canvas=tk.Canvas(
            self._wave_bg,width=168,height=38,
            bg=BG,highlightthickness=0
        )
        self._wave_canvas.place(x=12,y=0)
        self._wave_label=tk.Label(
            self._wave_bg,text="SLEEPING...",
            font=("Courier New",8),
            bg=BG,fg=DIM
        )
        self._wave_label.place(x=190,y=12)
        self._sep3=tk.Frame(self.root,bg=BORDER,height=1)
        self._sep3.place(x=0,y=301,width=W_GUI)
        self._ftr=tk.Frame(self.root,bg=BG2,height=26)
        self._ftr.place(x=0,y=302,width=W_GUI)

        tk.Label(self._ftr,text="PC: USER // SYS NOMINAL",
                 font=("Courier New",7),
                 bg=BG2,fg=DIM).place(x=14,y=6)
        
        self._clock_var=tk.StringVar(value="--:--:-- --")
        tk.Label(self._ftr,textvariable=self._clock_var,
                 font=("Courier New",7),
                bg=BG2,fg=DIM).place(relx=0.5,y=6,anchor="n")
        
        self._uptime_var=tk.StringVar(value="-UPTIME: 00:00")
        tk.Label(self._ftr,textvariable=self._uptime_var,
                 font=("Courier New",7),
                bg=BG2,fg=GREEN).place(relx=1.0,x=-14,y=6,anchor="ne")
        

        self._btn_min=tk.Button(
            self.root,text="—",
            font=("Courier New",10),
            bg=BG2,fg=DIM,
            activebackground=BG2,activeforeground=BLUE,
            bd=0,cursor="hand2",
            command=self.minimize
        )
        self._btn_full=tk.Button(
            self.root,text="⛶",
            font=("Courier New",10),
            bg=BG2,fg=DIM,
            activebackground=BG2,activeforeground=BLUE,
            bd=0,cursor="hand2",
            command=self.toggle_mode
        )
        self._btn_close=tk.Button(
            self.root,text="✕",
            font=("Courier New",10),
            bg=BG2,fg=DIM,
            activebackground=BG2,activeforeground="#e04060",
            bd=0,cursor="hand2",
            command=self.hide
        )
        self._layout_controls(W_GUI)

        self.bg.create_rectangle(
            0,0,W_GUI-1,H_GUI-1,
            outline=BORDER,width=1,tags="border"
        )

    def _build_grips(self):
        cursors={
            "n":"size_ns","s":"size_ns",
            "w":"size_we","e":"size_we",
            "nw":"size_nw_se","se":"size_nw_se",
            "ne":"size_ne_sw","sw":"size_ne_sw",
        }
        self._grips={}
        for edge,cur in cursors.items():
            g=tk.Frame(self.root,bg=BORDER,cursor=cur)
            g.bind("<ButtonPress-1>",lambda e,ed=edge:self._start_resize(e,ed))
            g.bind("<B1-Motion>",self._do_resize)
            self._grips[edge]=g

    def _start_resize(self,e,edge):
        self._rs=(edge,e.x_root,e.y_root,
                  self.root.winfo_x(),self.root.winfo_y(),
                  self.root.winfo_width(),self.root.winfo_height())
        return "break"

    def _do_resize(self,e):
        if not self._rs:
            return "break"
        edge,sx,sy,x,y,w,h=self._rs
        dx=e.x_root-sx
        dy=e.y_root-sy
        nw,nh=w,h
        if "e" in edge:
            nw=w+dx
        if "w" in edge:
            nw=w-dx
        if "s" in edge:
            nh=h+dy
        if "n" in edge:
            nh=h-dy
        nw=max(MIN_W,nw)
        nh=max(MIN_H,nh)
        nx=x+w-nw if "w" in edge else x
        ny=y+h-nh if "n" in edge else y
        self.root.geometry(f"{nw}x{nh}+{nx}+{ny}")
        return "break"

    def _layout_grips(self,W,H):
        if self._maximized:
            for g in self._grips.values():
                g.place_forget()
            return
        t,c=EDGE,CORNER
        spots={
            "n":(c,0,W-2*c,t),
            "s":(c,H-t,W-2*c,t),
            "w":(0,c,t,H-2*c),
            "e":(W-t,c,t,H-2*c),
            "nw":(0,0,c,c),
            "ne":(W-c,0,c,c),
            "sw":(0,H-c,c,c),
            "se":(W-c,H-c,c,c),
        }
        for edge,(x,y,w,h) in spots.items():
            g=self._grips[edge]
            g.place(x=x,y=y,width=max(1,w),height=max(1,h))
            g.lift()
        for b in (self._btn_min,self._btn_full,self._btn_close):
            b.lift()

    def _on_configure(self,e):
        if e.widget is not self.root:
            return
        size=(e.width,e.height)
        if size==self._size:
            return
        self._size=size
        self._relayout(*size)

    def _relayout(self,W,H):
        strip=int(H*0.25)
        chat_h=H-176-strip
        body=chat_h>=60

        self.bg.place(x=0,y=0,width=W,height=H)
        self.bg.coords("border",0,0,W-1,H-1)
        self._hdr.place(x=0,y=0,width=W)
        self._sep0.place(x=0,y=44,width=W)
        self._layout_controls(W)

        body_widgets=[self._stats_bg,self._sep1,self._chat_frame,
                      self._sep2,self._wave_bg,self._sep3,self._ftr]
        if not body:
            for w in body_widgets:
                w.place_forget()
        else:
            fw=(W-2)//3
            self._bar_max=max(20,fw-24)
            self._stats_bg.place(x=0,y=45,width=W,height=64)
            for i,f in enumerate(self._stat_frames):
                f.place(x=i*(fw+1),y=0,width=fw,height=64)
            for bb in self._bar_bgs:
                bb.place(x=10,y=56,width=self._bar_max,height=2)
            self._sep1.place(x=0,y=109,width=W)
            self._chat_frame.place(x=0,y=110,width=W,height=chat_h)
            y=110+chat_h
            self._sep2.place(x=0,y=y,width=W)
            self._wave_bg.place(x=0,y=y+1,width=W,height=38)
            self._sep3.place(x=0,y=y+39,width=W)
            self._ftr.place(x=0,y=y+40,width=W,height=26)
            self._apply_bars()

            fs=max(8,min(18,int(9*min(W/W_GUI,H/H_GUI)+0.5)))
            if fs!=self._chat_fs:
                self._chat_fs=fs
                self._chat.config(font=("Courier New",fs))

        self._layout_grips(W,H)

    def _draw_pill(self):
        c=self._pill_canvas
        c.delete("all")
        palette={
            "ACTIVE": (GREEN,"#001a0a"),
            "LISTENING":(BLUE,"#00101a"),
            "SLEEPING": (DIM,BG2),
        }

        col,bg_col=palette.get(self.status,(DIM,BG2))

        c.create_rectangle(0,0,136,26,fill=bg_col,outline=col,width=1)

        c.create_oval(10,9,20,19,fill=col,outline="")
        c.create_text(70,13,text=self.status,
                      font=("Courier New",9,"bold"),
                      fill=col,anchor="center")
        

    def set_status(self,status:str):

        self.status=status.upper()
        self.root.after(0,self._draw_pill)
        labels={
            "ACTIVE":   ("PROCESSING...",GREEN),
            "LISTENING": ("LISTENING...",BLUE),
            "SLEEPING":("SLEEPING...", DIM),
        }
        txt,col=labels.get(self.status,("...",DIM))
        self.root.after(0,lambda: self._wave_label.config(text=txt,fg=col))

    def  add_message(self,sender:str,text:str):
        def _insert():
            self._chat.config(state="normal")
            if sender=="you":
                self._chat.insert("end",">","pre_you")
                self._chat.insert("end",text+"\n","txt_you")
            elif sender== "jarvis":
                self._chat.insert("end","JARVIS: ","pre_jarvis")
                self._chat.insert("end",text+ "\n","txt_jarvis")
            else:
                self._chat.insert("end",f"[{text}]\n","sys")
            self._chat.config(state="disabled")
            self._chat.see("end")
        self.root.after(0,_insert)

    def _apply_bars(self):
        for key,val in self._stat_vals.items():
            bar,color=self._stat_bars[key]
            if key=="bat" and val<20 and not self._charging:
                bar.config(bg="#ffaa00")
            else:
                bar.config(bg=color)
            bar.config(width=int(val/100*self._bar_max))
    
    def _tick_stats(self):
        cpu=psutil.cpu_percent()
        ram=psutil.virtual_memory().percent
        bat=psutil.sensors_battery()
        bat_pct=int(bat.percent) if bat else 0
        self._charging= bat.power_plugged if bat else False

        self._cpu_var.set(f"{int(cpu)}%")
        self._ram_var.set(f"{int(ram)}%")
        self._bat_var.set(f"{bat_pct}%")

        self._stat_vals={"cpu":cpu,"ram":ram,"bat":bat_pct}
        self._apply_bars()
        self.root.after(2000,self._tick_stats)
    
    def _tick_clock(self):
        now=datetime.datetime.now()
        self._clock_var.set(now.strftime("%I:%M:%S %p"))

        up=int(time.time()-self.start_ts)
        h,rem=divmod(up,3600)
        m,s=divmod(rem,60)
        if h:
            self._uptime_var.set(f"UPTIME: {h:02d}: {m:02d}:{s:02d}")
        else:
            self._uptime_var.set(f"UPTIME: {m:02d}:{s:02d}")

        self.root.after(1000,self._tick_clock)
    
    def _tick_animation(self):
        self._draw_hud()
        self._draw_wave()
        self._angle+=0.018
        self._wave_t+=0.045
        self.root.after(40,self._tick_animation)
    

    def _draw_hud(self):
        c=self.bg
        ang=self._angle
        W=self.bg.winfo_width()
        H=self.bg.winfo_height()
        if W<10 or H<10:
            return
        scale=min(W,H)/440

        c.delete("hud")
        hex_r=19
        hex_w=hex_r*math.sqrt(3)
        hex_h=hex_r*2
        for row in range(-1, int(H/(hex_h*0.75))+2):
            for col in range(-1,int(W*0.58/hex_w)+2):
                hx=col*hex_w+(row%2)*hex_w*0.5
                hy=row*hex_h*0.75
                pts=_hex_points(hx,hy,hex_r-1)
                c.create_polygon(pts,outline="#041828",
                                fill="",width=1,tags="hud")
        

        cx,cy=int (W*0.74) if W<600 else int(W*0.82),int(H*.54) if H<500 else int(H*0.65)
        for i in range(36):
            a=(i/36)*math.pi*2
            x2=cx+math.cos(a)*W
            y2=cy+math.sin(a)*W
            c.create_line(cx,cy,x2,y2,
                          fill="#03182e",width=1,tags="hud")
        ring_defs=[
            (int(148*scale),"#0a2a45",1),
            (int(118*scale),"#0c3050",1),
            (int(88*scale),"#0e3860",1),
            (int(60*scale),"#105080",1),
            (int(36*scale),"#1060a0",1),
        ]
        for r, col, lw in ring_defs:
            c.create_oval(cx-r,cy-r,cx+r,cy+r,
                          outline=col,width=lw,tags="hud")
            
        seg_r=int(162*scale)
        n_seg=60
        for i in range(n_seg):
            a1=(i/n_seg)*2*math.pi+ang*0.35
            a2=a1+(2*math.pi/n_seg)*0.68
            brigthness=(math.sin(ang*2.5+i*.42)+1)/2
            alpha_hex=format(int(40+brigthness*80),'02x')
            col=f"#00{format(int(130+brigthness*80),'02x')}{format(int(180+brigthness*60),'02x')}"
            x1=cx+math.cos(a1)*seg_r
            y1=cy+math.sin(a1)*seg_r
            x2=cx+math.cos(a2)*seg_r
            y2=cy+math.sin(a2)*seg_r
            steps=4
            pts_arc=[]
            for s in range(steps+1):
                aa= a1+(a2-a1)*s/steps
                pts_arc.extend([cx+math.cos(aa)*seg_r,
                                cy+math.sin(aa)*seg_r])
            if len(pts_arc)>=4:
                c.create_line(*pts_arc,fill=col,
                              width=2,tags="hud",smooth=True)
                
        dash_r=int(178*scale)
        for i in range(28):
            a1=(i/28)*2*math.pi-ang*0.18
            a2=a1+(2*math.pi/28)*0.55
            steps=3
            pts_arc=[]
            for s in range(steps+1):
                aa=a1+(a2-a1)*s/steps
                pts_arc.extend([cx+math.cos(aa)*dash_r,
                                cy+math.sin(aa)*dash_r])
            if len(pts_arc)>=4:
                c.create_line(*pts_arc,fill="#0a304a",
                              width=1,tags="hud",smooth=True)
        
        for i in range(8):
            a=(i/8)*math.pi*2+ang*0.55
            x1=cx+math.cos(a)*(36*scale)
            y1=cy+math.sin(a)*(36*scale)
            x2=cx+math.cos(a)*(85*scale)
            y2=cy+math.sin(a)*(85*scale)
            
            c.create_line(x1,y1,x2,y2,
                          fill="#0a4060",width=1,tags="hud")
        
        sweep_a=ang*0.9
        spread=0.55
        pts_sweep=[cx,cy]
        steps=10
        for s in range(steps+1):
            aa=sweep_a+spread*s/steps
            pts_sweep.extend([cx+math.cos(aa)*int(148*scale),
                              cy+math.sin(aa)*int(148*scale)])
        if len(pts_sweep)>=6:
            c.create_polygon(pts_sweep,fill="#001a30",
                             outline="",tags="hud")
        
        c.create_line(
            cx,cy,
            cx+math.cos(sweep_a+spread)*int(152*scale),
            cy+math.sin(sweep_a+spread)*int(152*scale),
            fill="#0060a0", width=2,tags="hud"
        )

        glow_steps=8
        for g in range(glow_steps,0,-1):
            r_g=g*int(4*scale)
            frac=g/glow_steps
            blue=int(100+frac*155)
            col=f"#00{format(int(frac*180),'02x')}{format(blue,'02x')}"
            c.create_oval(cx-r_g,cy-r_g,cx+r_g,cy+r_g,
                          fill=col,outline="",tags="hud")
        
        dx,dy,dr=int(W*0.1),int(H*0.22),int(26*scale)
        c.create_oval(dx-dr,dy-dr,dx+dr,dy+dr,
                      outline="#082840",width=1,tags="hud")
        for i in range(12):
            a=(i/12)*math.pi*2-ang*1.1
            ix=dx+math.cos(a)*dr*0.58
            iy=dy+math.sin(a)*dr*0.58
            ox=dx+math.cos(a)*dr*0.9
            oy=dy+math.sin(a)*dr*0.9
            c.create_line(ix,iy,ox,oy,
                          fill="#093555",width=1,tags="hud")
        dx2,dy2,dr2=int(W*0.28),int(H*0.14),int(14*scale)
        c.create_oval(dx2-dr2,dy2-dr2,dx2+dr2,dy2+dr2,
                      outline="#082840",width=1,tags="hud")
        for i in range(8):
            a=(i/8)*math.pi*2+ang*1.6
            ox=dx2+math.cos(a)*dr2*0.85
            oy=dy2+math.sin(a)*dr2*0.85
            ix=dx2+math.cos(a)*dr2*0.55
            iy=dy2+math.sin(a)*dr2*0.55
            c.create_line(ix,iy,ox,oy,
                          fill="#093555",width=1,tags="hud")
        
        scan_y=int((time.time()*55)%H)
        c.create_rectangle(0,scan_y-4,W,scan_y+4,
                           fill="#04111f",outline="",tags="hud")
        blen=22
        corners=[
            (1  ,1  ,1  ,1  ),
            (W-2,1  ,-1 ,1  ),
            (1  ,H-2,1  ,-1 ),
            (W-2,H-2,-1 ,-1 ),
        ]
        for bx,by,sx,sy in corners:
            c.create_line(bx,by,bx+sx*blen,by,
                          fill="#0d4a6e",width=1,tags="hud")
            c.create_line(bx,by,bx,by+sy*blen,
                          fill="#0d4a6e",width=1,tags="hud")
   
    def _draw_wave(self):
        wc=self._wave_canvas
        wt=self._wave_t
        active=self.status in ("LISTENING","ACTIVE")
        col=BLUE if self.status=="LISTENING" else\
        GREEN if self.status=="ACTIVE" else DIM2

        wc.delete("all")
        for i in range(12):
            phase=wt*5+i*0.55
            h_bar=int(abs(math.sin(phase))*16)+3 if active else 3
            x1=4+i*13
            x2=x1+5
            y1=19-h_bar
            y2=19+h_bar
            wc.create_rectangle(x1,y1,x2,y2,
                                fill=col,outline="",tags="bar")

    def _layout_controls(self,width):
        self._btn_min.place(x=width-84,y=8)
        self._btn_full.place(x=width-58,y=8)
        self._btn_close.place(x=width-32,y=8)
        self._pill_canvas.place(x=width-84-136-10,y=9)
        for b in (self._btn_min,self._btn_full,self._btn_close):
            b.lift()

    def minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def _on_map(self,e):
        if e.widget is self.root and not self.root.overrideredirect():
            self.root.after(10,self._restore_frameless)

    def _restore_frameless(self):
        self.root.overrideredirect(True)
        self.root.lift()
        self.root.attributes("-topmost",True)

    def hide(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost",True)
    
    def toggle_mode(self):
        if not self._maximized:
            self._restore_geom=self.root.geometry()
            self._maximized=True
            sw=self.root.winfo_screenwidth()
            sh=self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
        else:
            self._maximized=False
            self.root.geometry(self._restore_geom or f"{W_GUI}x{H_GUI}+400+200")
        self._relayout(self.root.winfo_width(),self.root.winfo_height())

    def run(self):
        self.root.mainloop()

def _make_tray_icon():
    img=Image.new("RGBA",(64,64),(0,0,0,0))
    d=ImageDraw.Draw(img)
    d.ellipse([3,3,61,61],outline=(0,204,255,255),width=3)

    d.ellipse([14,14,50,50],outline=(0,255,136,200),width=2)

    d.ellipse([25,25,39,39],fill=(0,180,255,255))
    return img

def _run_tray(gui:JarvisGUI):
    if not TRAY_AVAILABLE:
        return
    
    def on_show(icon,item):
        gui.show()
    def on_exit(icon,item):
        icon.stop()
        os._exit(0)

    icon=pystray.Icon(
        "JARVIS",
        _make_tray_icon(),
        "J.A.R.V.I.S",
        menu=pystray.Menu(
            pystray.MenuItem("Show JARVIS",on_show,default=True),
            pystray.MenuItem("Exit JARVIS", on_exit),
        ),
    )
    icon.run()


_gui_instance:JarvisGUI|None=None

def launch_gui()-> JarvisGUI:
    global _gui_instance
    _gui_instance=JarvisGUI()

    tray_thhread=threading.Thread(
        target=_run_tray,args=(_gui_instance,),daemon=True
    )
    tray_thhread.start()
    _gui_instance.run()
    return _gui_instance

def get_gui()->JarvisGUI|None:
    return _gui_instance

if __name__=="__main__":
    gui=JarvisGUI()

    gui.root.after(800,lambda:gui.add_message("you", "jarvis, open, Chrome"))
    gui.root.after(1400,lambda:[gui.set_status("ACTIVE"),
                                gui.add_message("jarvis","opening chrome, sir")])
    gui.root.after(2600,lambda:[gui.set_status("LISTENING"),
                                gui.add_message("you","what's the battery level?")])
    gui.root.after(3400,lambda:gui.add_message("jarvis","battery is at current charge level."))
    gui.root.after(4500,lambda:[gui.set_status("SLEEPING"),
                                gui.add_message("sys", "jarvis is now sleeping...")])
    gui.root.after(6000,lambda:gui.set_status("LISTENING"))

    if TRAY_AVAILABLE:
        tray_thread=threading.Thread(target=_run_tray,args=(gui,),daemon=True)
        tray_thread.start()
    gui.run()