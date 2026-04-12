#"what to be noted in coding expecially looping is always counting "
#"and we can't do anythig with a data in a data set unless we bring it out with loop  "
#minutes=1
#while minutes <=60:
 #if minutes==31:
  #  print("stop")
    #break
#import time 
#minute=int(input("enter number"))
#while minute<=60:
 #   if minute == minute:
  #      if minute < 9:
   #         time.sleep(50)
    #        print("time is almost up ")
     #   print("stop")
      #  break
#code to check if you are adult
#age=int(input("enter your age:"))
#if age >=18:
#    print("you are an adult")
#else:
 #   print("you are a minor")
#error code need chatgpt
#a=[1,2,3,4,5,6,7,8,9]
#for x in a:
# all=sum(x)
# print(all) 
#error code need chatgpt
#def square(number):
 #   return a+b
#result=(5,3)
#print(result)
#correct code 
#name=input("enter your name:")
#print("welcome",name)

#a={1,2,3,4,5}
#b=a[0]
#print(b)
#need to catch error
#a=int(input("enter your number:"))
#if a % 2==0: 
#    print("even number")
#elif a % 2 !=0:
#    print("odd number")
#else:
#    print("prime number")
#index error code need chatgpt
#a=["rice","beans","yam","spag"]
#print(a[0,2])
# correct looping
#for i in range (5):
 #print(i)

#import tkinter as me
#from tkinter import messagebox
#def decrement ():
#    try:
#        num=int(txtnum.get())
#        output.delete("1.0",me.END)
#        while num > 0:
#            output.insert(me.END,str(num)+"\n")
#          num-=1
#    except ValueError:
   #     messagebox.showinfo("error","enter valid info")
   # except AttributeError:
  #      messagebox.showinfo("error","use your sense")
  #  except ZeroDivisionError:
  #      messagebox.showinfo("error","enter valid number")
#root=me.Tk()
#root.title("Decrement")
#me.Label(root, text="Enter numer:").grid(column=0,row=0,padx=10,pady=5)
#txtnum=me.Entry(root)
#txtnum.grid (row=0, column=1, padx=10, pady=5)
#me.Button(root,text="oya",command=decrement).grid(row=1,column=0,columnspan=2,padx=10)
#output=me.Text(root,height=10,width=20)
#output.grid(row=2,column=0,columnspan=2,padx=10,pady=10)
#root.mainloop()

a=[1,2,3,4,5]
for b in a:
     if b in [3]:
          break
     print(b)

#a=[1,2,3,4,5]
#print(a[0])
  