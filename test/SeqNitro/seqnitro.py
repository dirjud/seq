import nitro,seq
from seq import SeqNitro, Bin, Sequence as Seq

term = nitro.Terminal(name="test_term")

bin1 = Bin.Bin(
    name="bin1",
    regs = [ seq.Signal(name="a",width=1, init=0), 
             seq.Signal(name="b",width=10,init=0), 
             seq.Signal(name="c",width=1, init=0), 
             ],
    children=[],
    seqs = [
        SeqNitro.Set(name="abc", terminal=term, set=dict(a=1, b=300,c=1)),
        Seq.Set(name="abc2", set=dict(a=0, b=101, c=1)),
        Seq.Set(name="abc3", set=dict(a=1, b=222, c=0)),
        ]
    )


bin2 = Bin.Bin(
    name="bin2",
    regs = [ ],
    children=[bin1],
    seqs = [
        SeqNitro.Serial(name="bin1_seqs", terminal=term, 
                        subseqs=["abc2", "abc3",],
                        extra=2)
        ]
    )

bin2.vlog_dump(recurse=True)

di = nitro.DeviceInterface(name="test_di", terminal_list=[term,])
nitro.XmlWriter("test.xml").write(di)
