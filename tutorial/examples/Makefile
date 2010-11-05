

%.v: %.py
	python $< $@ 

all: example1.v
	iverilog -o example1_tb.vvp example1_tb.v example1.v example1_manual.v
	vvp example1_tb.vvp


clean:
	rm -f *~ *.vvp *.vcd