import threading
import json
import Queue
import random
import math
import time
import Tkinter
import tkMessageBox
import tkFont
import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk

from ArduinoSerMntr import*


class App:
    # Ininitalization
    def __init__(self , queue, frame , width , height , root):
        self.ArdMntr= MonitorThread()
        self.ArdMntr.start()
        myfont14 = tkFont.Font(family="Verdana", size=14)
        myfont12 = tkFont.Font(family="Verdana", size=12)
        self.root = root
        
        self.screen_width, self.screen_height = width, height
        #self.frame_width, self.frame_height= int(width*0.79), height
        btn_width, btn_height= 15, 1
        self.interval_x, self.interval_y= 6, 6
        #print width,',', height,' ; ',btn_width,',', btn_height
        
        # ====== Configuration ============
        self.lbl_CurrCoord= Tkinter.Label(self.root, text="[ Current Position ]",     font= myfont14)
        self.lbl_CurrCoord.place(x= self.interval_x, y= self.interval_y)
        self.root.update()
        self.lbl_CurrPos= Tkinter.Label(self.root, text="(X, Y)= (-1, -1)",font= myfont12)
        self.lbl_CurrPos.place(x= self.interval_x, y= self.lbl_CurrCoord.winfo_y()+ self.lbl_CurrCoord.winfo_height())
        self.root.update()
        self.lbl_MoveCoord= Tkinter.Label(self.root, text="[ Step Motor Control ]", font= myfont14)
        self.lbl_MoveCoord.place(x= self.interval_x, y= self.lbl_CurrPos.winfo_y()+ self.lbl_CurrPos.winfo_height()+self.interval_y)
        self.root.update()

        self.lbl_Xpos= Tkinter.Label(self.root, text= 'X :',font= myfont14)
        self.lbl_Xpos.place(x= self.interval_x, y = self.lbl_MoveCoord.winfo_y()+ self.lbl_MoveCoord.winfo_height()+ self.interval_y)
        self.root.update()
        self.entry_Xpos= Tkinter.Entry(self.root, font= myfont14, width=4)
        self.entry_Xpos.insert(Tkinter.END, "0")
        self.entry_Xpos.place(x= self.lbl_Xpos.winfo_x()+ self.lbl_Xpos.winfo_width(), y= self.lbl_Xpos.winfo_y())
        self.root.update()
        self.lbl_Ypos= Tkinter.Label(self.root, text= 'Y :',font= myfont14)
        self.lbl_Ypos.place(x= self.entry_Xpos.winfo_x()+ self.entry_Xpos.winfo_width()+ self.interval_x, y = self.lbl_Xpos.winfo_y())
        self.root.update()
        self.entry_Ypos= Tkinter.Entry(self.root, font= myfont14, width=4)
        self.entry_Ypos.insert(Tkinter.END, "0")
        self.entry_Ypos.place(x= self.lbl_Ypos.winfo_x()+ self.lbl_Ypos.winfo_width(), y= self.lbl_Ypos.winfo_y())
        self.root.update()
        self.lbl_posUnit= Tkinter.Label(self.root, text='(step)')
        self.lbl_posUnit.place(x= self.entry_Ypos.winfo_x()+ self.entry_Ypos.winfo_width(), y= self.entry_Ypos.winfo_y()+self.interval_y)

        self.btn_MoveTo= Tkinter.Button(self.root, text= 'Move to', command= self.btn_MoveTo_click,font= myfont14)
        self.btn_MoveTo.place(x= self.lbl_Xpos.winfo_x(), y=self.lbl_Ypos.winfo_y()+ self.lbl_Ypos.winfo_height()+ self.interval_y)
        self.root.update()

        self.btn_clear= Tkinter.Button(self.root, text='Clear Image', command= self.btn_clear_click,font= myfont14, width= btn_width, height= btn_height)
        #self.btn_clear.grid(row=0, column=1, sticky = Tkinter.W)
        self.btn_clear.place(x= self.lbl_MoveCoord.winfo_x(), y= self.screen_height- 120)
        self.root.update()
        self.btn_saveImg= Tkinter.Button(self.root, text='Save Image', command= self.btn_saveImg_click,font= myfont14, width= btn_width, height= btn_height)
        self.btn_saveImg.place(x= self.lbl_MoveCoord.winfo_x(), y= self.screen_height- btn_height- 70)
        self.root.update()

        #===== Image Frame ======
        self.frame_width, self.frame_height= self.screen_width-self.lbl_MoveCoord.winfo_width()- self.interval_x*4, height-5
        frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
        result = Image.fromarray(frame)
        result = ImageTk.PhotoImage(result)
        self.panel = Tkinter.Label(self.root , image = result)
        self.panel.image = frame
        self.panel.place(x=self.lbl_MoveCoord.winfo_width()+ self.interval_x*2, y= 0)
        #self.panel.grid(row=0, column=0)
        #self.panel.pack(side = Tkinter.LEFT)

        self.queue = queue
        # ====== UI callback setting ======
        self.panel.after(50, self.check_queue)
        self.lbl_CurrPos.after(5, self.UI_callback)
        #====== Override CLOSE function ==============
        self.root.protocol('WM_DELETE_WINDOW',self.on_exit)
        #=============================================
        self.mode= 0
        self.saveImg= False
        self.drawing= False
        self.x1, self.y1, self.x2, self.y2= -1,-1,-1,-1        
        self.line_info=[]

    # Override CLOSE function
    def on_exit(self):
        """When you click to exit, this function is called"""
        if tkMessageBox.askyesno("Exit", "Do you want to quit the application?"):
            print 'Close Arduino Thread...'
            self.ArdMntr.exit= True
            self.root.destroy()

    def UI_callback(self):
        tmp_text= '(X, Y)= ('+self.ArdMntr.cmd_state.strCurX+', '+self.ArdMntr.cmd_state.strCurY+')'
        self.lbl_CurrPos.config(text= tmp_text)
        self.lbl_CurrPos.after(10,self.UI_callback)
        #if self.ArdMntr.cmd_state.is_ready():
            #return 0

    def store(self):
        data = dict()
        data["x_min"] = self.x_min.get()
        data["y_min"] = self.y_min.get()
        data["x_max"] = self.x_max.get()
        data["y_max"] = self.y_max.get()
        with open("detect_area.json" , 'w') as out:
            json.dump(data , out)
        print "detect area set"
        #self.scales.destroy()

    def set_frame(self, frame):
        self.frame= frame

    
    def btn_saveImg_click(self):
        self.saveImg= True
        #cv2.imwrite('Frame1.png',frame)

    def btn_MoveTo_click(self):
        try:
            Target_X= int(self.entry_Xpos.get())
            Target_Y= int(self.entry_Ypos.get())
            #print Target_X, ' , ', Target_Y 
            if (Target_X>=0) & (Target_X<=8000) & (Target_Y>=0) & (Target_Y<=9500):
                cmd= 'G00 X{0} Y{1}'.format(Target_X, Target_Y)
                self.ArdMntr.serial_send(cmd)
                print 'Command: ', cmd
                
            else:
                tkMessageBox.showerror("Error", "The range of X should be in [0~8,000]\nThe range of Y should be in [0~9,500]")
            
            #print Target_X, ' , ',Target_Y
        except:
            tkMessageBox.showerror("Error", "Please enter number!")
        

    def btn_clear_click(self):
        self.line_info= []

    def mark_cross_line(self , frame):
        w = frame.shape[0] / 2
        h = frame.shape[1] / 2
        cv2.line(frame , (h - 15 , w) , (h + 15 , w) , (255 , 0 , 0) , 1)
        cv2.line(frame , (h , w - 15) , (h , w + 15) , (255 , 0 , 0) , 1)
        return frame


    def check_queue(self):
        try:
            frame = self.queue.get(block=False)
        except Queue.Empty:
            pass
        else:
            angle_beg=0
            angle_end=0
            frame = self.mark_cross_line(frame)
	    frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)

            if self.saveImg== True:
                tmp= cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite('Frame1.png',tmp)
                self.saveImg= False
            text=''
            if self.ArdMntr.cmd_state.is_ready():
                text= 'Idling ...'
                color = (0 , 255 , 0)
            else:
                text= 'Moving ...'
                color = (255,0,0)
            #text= text + '('+self.ArdMntr.cmd_state.strCurX+', '+self.ArdMntr.cmd_state.strCurY+')'
            cv2.putText(frame, text,(10,40),cv2.FONT_HERSHEY_SIMPLEX, 1,color,2)
            result = Image.fromarray(frame)
            result = ImageTk.PhotoImage(result)
            self.panel.configure(image = result)
            self.panel.image = result
        self.panel.after(1, self.check_queue)

def queue_create(queue, running , app , cap):
    #global cap
    while running:
        ret , frame = cap.read()
        frame = cv2.cvtColor(frame , cv2.COLOR_BGR2RGB)
        queue.put(frame)
        #app.set_frame(frame)
        time.sleep(0.01)

def run(cap):
    running = [True]

    root = Tkinter.Tk()
    root.title("[Arduino] Stepper Control")
    root.attributes('-zoomed', True) # FullScreen


    queue = Queue.LifoQueue(5)
    ret , frame = cap.read()
    
    app = App(queue , frame, root.winfo_screenwidth() , root.winfo_screenheight(), root)
    app.panel.bind('<Destroy>', lambda x: (running.pop(), x.widget.destroy()))

    thread = threading.Thread(target=queue_create, args=(queue, running , app , cap))
    thread.start()

    root.mainloop()



cap = cv2.VideoCapture(0)
run(cap)
