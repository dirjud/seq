all:
	python buf_ctl.py
	iverilog -o buf_ctl.vvp buf_ctl_tb.v buf_ctl.v capture_buf.v read_buf.v
	python buf_ctl_check.py

clean:
	rm -f capture_buf.v read_buf.v buf_ctl.v buf_ctl.vvp *~


