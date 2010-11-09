import seq
from seq import Bin, Sequence

# test unsigned and unsigned multiplication with full output width
a1 = seq.Signal("a1", width=4)
b1 = seq.Signal("b1", width=4)
a2 = seq.Signal("a2", width=4, signed=True)
b2 = seq.Signal("b2", width=4, signed=True)

# outputs that equal calculation
out1 = seq.Signal("out1",  width=8, signed=False)
out2 = seq.Signal("out2",  width=8, signed=True)

# outputs narrowed than calculation
out3 = seq.Signal("out3",  width=6, signed=False)
out4 = seq.Signal("out4",  width=6, signed=True)
out5 = seq.Signal("out5",  width=6, signed=False)
out6 = seq.Signal("out6",  width=6, signed=True)
out7 = seq.Signal("out7",  width=6, signed=False)
out8 = seq.Signal("out8",  width=6, signed=True)
out9 = seq.Signal("out9",  width=6, signed=False)
out10= seq.Signal("out10", width=6, signed=True)

# output wider than calculation
out11= seq.Signal("out11", width=10, signed=False)
out12= seq.Signal("out12", width=10, signed=True)
out13= seq.Signal("out13", width=10, signed=False)
out14= seq.Signal("out14", width=10, signed=True)

test1 = Bin.Bin(
    name = "test1",
    regs = [ out1, out2, out3, out4, out5, out6, out7, out8, out9, out10, out11, out12, out13, out14, ],
    seqs = [
        Sequence.Multiply(a=a1, b=b1, out=out1),
        Sequence.Multiply(a=a2, b=b2, out=out2),
        Sequence.Multiply(a=a1, b=b1, out=out3,  justify="right", clamp=False),
        Sequence.Multiply(a=a2, b=b2, out=out4,  justify="right", clamp=False),
        Sequence.Multiply(a=a1, b=b1, out=out5,  justify="left",  clamp=False),
        Sequence.Multiply(a=a2, b=b2, out=out6,  justify="left",  clamp=False),
        Sequence.Multiply(a=a1, b=b1, out=out7,  justify="right", clamp=True),
        Sequence.Multiply(a=a2, b=b2, out=out8,  justify="right", clamp=True),
        Sequence.Multiply(a=a1, b=b1, out=out9,  justify="left",  clamp=True),
        Sequence.Multiply(a=a2, b=b2, out=out10, justify="left",  clamp=True),
        Sequence.Multiply(a=a1, b=b1, out=out11, justify="right"),
        Sequence.Multiply(a=a2, b=b2, out=out12, justify="right"),
        Sequence.Multiply(a=a1, b=b1, out=out13, justify="left"),
        Sequence.Multiply(a=a2, b=b2, out=out14, justify="left"),
        ]
    )
test1.vlog_dump()


#Bin.Bin(name="test2", 
