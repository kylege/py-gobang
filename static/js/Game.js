var GameCanvas = function() {

	this.PIECE_NONE = 0;
	this.PIECE_BLACK = 1;
	this.PIECE_WHITE = 2;

	this.margin = 30;
	this.grid_count = 15;
	this.line_width = 0.2;
	this.out_width = 5;
	this.grid_width = this.margin * this.grid_count + 10; //460

	this.canvas = document.getElementById('game-canvas');
	this.context = this.canvas.getContext('2d');
	

	/**
	 * 画棋盘
	 * @return 
	 */
	this.drawGrid = function() {
		this.context.fillStyle = "#fff";
		this.context.strokeStyle = "#22252B";
		this.context.lineWidth = this.line_width;
		this.context.beginPath();
		for(i=0; i<=this.grid_count; i++) { //横线
			this.context.moveTo(this.out_width, this.margin * i + this.out_width);
			this.context.lineTo(this.grid_width-this.out_width, this.margin * i + this.out_width);
		}
		for(i=0; i<=this.grid_count; i++) {
			this.context.moveTo(this.margin*i+this.out_width, this.out_width);
			this.context.lineTo(this.margin*i+this.out_width, this.grid_width-this.out_width);
		}
		this.context.stroke();
	}
	
	/**
	 * 画棋子	
	 * @param  int grid_no_x 第几行 从0开始
	 * @param  int grid_no_y 第几列
	 * @param int type 棋子类型，1黑2白
	 * @return bool
	 */
	this.drawPiece = function(grid_no_x, grid_no_y, type) {
		var corx = this.out_width + this.margin*grid_no_y;
		var cory = this.out_width + this.margin*grid_no_x;

		var canvas = document.getElementById('game-canvas');
		var context = canvas.getContext('2d'); 

		var destimg = new Image();
		destimg.onload = function(){
			context.drawImage(destimg, corx-14, cory-14, 28, 28);			
    	};

		if(type == this.PIECE_WHITE){
			destimg.src = "../static/img/white-28x28.png";
		}else if(type == this.PIECE_BLACK){
			destimg.src = "../static/img/black-28x28.png";
		}else{
			return false;
		}
		
    	return true;
	}
 
}
