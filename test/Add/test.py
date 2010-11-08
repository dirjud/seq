import seq
from seq import Bin, Sequence

a1 = seq.Signal("a1", width=4)
b1 = seq.Signal("b1", width=4)
out1 = seq.Signal("out1", width=5, signed=False)
a2 = seq.Signal("a2", width=4, signed=True)
b2 = seq.Signal("b2", width=4, signed=True)
out2 = seq.Signal("out2", width=5, signed=True)

out3 = seq.Signal("out3", width=4, signed=False)
out4 = seq.Signal("out4", width=4, signed=False)
out5 = seq.Signal("out5", width=3, signed=True)
out6 = seq.Signal("out6", width=4, signed=True)
out7 = seq.Signal("out7", width=20, signed=True)

test1 = Bin.Bin(
    name = "test1",
    regs = [ out1, out2, out3, out4, out5, out6, out7 ],
    seqs = [
        Sequence.Add(a=a1, b=b1, out="out1"),
        Sequence.Add(a=a2, b=b2, out="out2"),
        Sequence.Add(a=a1, b=b1, out="out3"),
        Sequence.Add(a=a1, b=b1, out="out4", clamp=True),
        Sequence.Add(a=a2, b=b2, out=out5,   clamp=True),
        Sequence.Add(a=a2, b=b2, out=out6,   clamp=True),
        Sequence.Add(a=a2, b=b2, out=out7,   clamp=True),
        ]
    )
test1.vlog_dump()
