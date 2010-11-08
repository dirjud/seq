import subprocess

out = subprocess.Popen(['vvp', "fir.vvp"], stdout=subprocess.PIPE).communicate()[0].split("\n")
if out[0].startswith("VCD info:"):
    out = out[1:]


xin = []
xout = []
for o in out:
    if(o):
        x = o.split(",")
        xin.append(int(x[0]))
        xout.append(int(x[1]))

buf = [ 0 ] * 16;
xoutIdeal = []
for x in xin:
    buf = [x] + buf[:-1]

    accum = 0;
    for b in buf:
        accum += b;
    xoutIdeal.append(accum/16)

print "ALL PASS=%d" % (xoutIdeal == xout,)

try:
    import numpy, pylab
    n = numpy.arange(len(xin))

    xoutI = numpy.convolve(numpy.ones(16)/16., xin, mode="full")[:len(xin)]

    import pylab
    pylab.plot(n, xin,'.-', label="Input")
    pylab.plot(n, xout,'.-', label="Output")
    #pylab.plot(n, xoutIdeal,'o', label="Ideal Output")
    pylab.grid(True)
    pylab.legend()
    pylab.title("FIR Filter Response to Random Noise Input");
    pylab.xlabel("Sample Number");
    pylab.ylabel("Sample Value");
    pylab.savefig("fir_example.png")

except ImportError:
    print "Warning: numpy and matplotlib not installed. Cannot produce plots."
