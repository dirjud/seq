all:
	python fir.py
	iverilog -o fir.vvp fir_tb.v fir_top.v fir.v fir_base.v
	python fir_check.py

clean:
	rm -f fir.v fir_base.v fir_example.png fir.vcd fir.vvp *~


