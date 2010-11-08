import seq
from seq import Bin, Sequence

# test unsigned and unsigned multiplication with full output width
a1 = seq.Signal("a1", width=4)
b1 = seq.Signal("b1", width=4)
out1 = seq.Signal("out1", width=8, signed=False)
out2 = seq.Signal("out2", width=8, signed=True)
out3 = seq.Signal("out3", width=6, signed=False)


test1 = Bin.Bin(
    name = "test1",
    regs = [ out1, out2, out3, ],
    seqs = [
        # generated an unsigned serial multiply sequence
        Sequence.SerialMultiply(a=a1, b=b1, out="out1"),
        
        # generate a signed serial multiply sequence
        Sequence.SerialMultiply(a=seq.Signal("a2", width=4, signed=True),
                                b=seq.Signal("b2", width=4, signed=True), 
                                out=out2),

        # generate an unsigned serial multiply sequence the is not full output
        # width but drops LSB's (left justified)
        Sequence.SerialMultiply(a=a1, b=b1, out="out3"),
        ]
    )
test1.vlog_dump()


#Bin.Bin(name="test2", 
