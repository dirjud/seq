module fir_top
  #(parameter DATA_WIDTH=8
    )
  (input clk,
   input reset_n,
   input [DATA_WIDTH-1:0] xin,
   input we,

   output running,
   output done,
   output [DATA_WIDTH-1:0] xout
   );

   localparam COEFF_WIDTH=8; // width of FIR tap coefficents. also set in the seq script
   localparam N = 5'd16; // number of taps in FIR filter, also set in the seq script
   localparam N_WIDTH = 5; // CEIL(LOG2(N)), also set in the seq script
   localparam FIR_OUT_WIDTH=20; // if you change this you also need to change the seq script
   
   // create buffers for input stream and coefficients
   reg [COEFF_WIDTH-1:0]   fir_coeffs[0:N-1];
   reg [DATA_WIDTH-1:0]    xin_buf[0:N-1];

   wire [FIR_OUT_WIDTH-1:0] xout_raw;
   wire 		    running_pre;
   assign running = running_pre | we_s;
   reg 			    we_s;

   wire [N_WIDTH-1:0] fir_addr;
   reg [N_WIDTH-1:0]  waddr;
   wire [N_WIDTH:0]   raddr = waddr + fir_addr;
   wire [N_WIDTH-1:0] xin_buf_addr = (we) ? waddr : (raddr >= N) ? raddr - N : raddr; // when writing, set the ram address to waddr, when reading, we need to make the read address a circular buffer, so we need to wrap the read addr modulo N
   reg [COEFF_WIDTH-1:0] 	    coeff;
   reg [DATA_WIDTH-1:0] 	    xin1;
   
   integer j;
   always @(posedge clk or negedge reset_n) begin
      if(!reset_n) begin
	 we_s <= 0;
	 coeff <= 0;
	 waddr <= 0;
	 xin1  <= 0;
	 for(j=0;j<N;j=j+1) begin
	    fir_coeffs[j] = 8;
	    xin_buf[j] = 0;
	 end
      end else begin
	 we_s <= we;
	 if(we) begin
	    xin_buf[xin_buf_addr] <= xin;
	 end else if(done) begin
	    if(waddr == N-1) begin
	       waddr <= 0;
	    end else begin
	       waddr <= waddr + 1;
	    end
	 end else begin
	    xin1 <= xin_buf[xin_buf_addr];
	 end
	 coeff <= fir_coeffs[fir_addr];
      end
   end
   
   fir fir
     (.clk				(clk),
      .reset_n				(reset_n),
      .coeff				(coeff),
      .xin				(xin1),
      .seq				(1'b0),
      .start				(we_s),
      .addr				(fir_addr),
      .xout				(xout_raw),
      .mult				(),
      .running				(running_pre),
      .done				(done)
      );

   localparam EXTRA_BITS = FIR_OUT_WIDTH - DATA_WIDTH - COEFF_WIDTH + 1;
   
   assign xout = xout_raw[FIR_OUT_WIDTH-EXTRA_BITS-1:FIR_OUT_WIDTH-EXTRA_BITS-DATA_WIDTH];
   
endmodule
   
   
   