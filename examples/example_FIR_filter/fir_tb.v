module fir_tb();
   reg clk, reset_n;
   always #1 clk=!clk;

   localparam DATA_WIDTH=8;
   wire signed [DATA_WIDTH-1:0] xout;
   reg signed [DATA_WIDTH-1:0]  xin;
   reg 				we;

   initial begin
      we  = 0;
      clk = 0;
      reset_n = 0;
      xin = -100;

      $dumpfile("fir.vcd");
      $dumpvars(0, fir_tb);
      
      
      repeat(4) @(posedge clk);
      reset_n <= 1;
      repeat(4) @(posedge clk);

      repeat(60) begin
	 xin = $random;
	 @(posedge clk) we <= 1;
	 @(posedge clk) we <= 0;
	 @(posedge clk);
	 while(running) @(posedge clk);
	 $display("%d, %d", xin, xout);
      end
      $finish;
   end
      

   fir_top #(.DATA_WIDTH(DATA_WIDTH))
   fir_top
     (.clk				(clk),
      .reset_n				(reset_n),
      .xin				(xin),
      .we				(we),
      .running				(running),
      .done				(done),
      .xout				(xout)
      );
   
   
   
endmodule