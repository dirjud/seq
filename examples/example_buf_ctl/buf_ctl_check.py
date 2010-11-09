import subprocess

out = subprocess.Popen(['vvp', "buf_ctl.vvp"], stdout=subprocess.PIPE).communicate()[0].split("\n")
if out[0].startswith("VCD info:"):
    out = out[1:-1]


xin = []
xout = []
for o in out:
    if(o):
        x = o.split(",")
        if(x[0] == "read"):
            xout.append( int(x[1].split("=")[1]))
        elif(x[0] == "capture"):
            xin.append( int(x[1].split("=")[1]))

xin = xin[:len(xout)]

print "ALL PASSED=%d" % ((xin==xout) and (len(xin)>1),)
