var offline_timeout;

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
			destimg.src = status_imgs[1];
		}else if(type == this.PIECE_BLACK){
			destimg.src = status_imgs[0];
		}else{
			return false;
		}
		
    	return true;
	}
 
}

function getGridRowCol(pos){
    var cursorx = pos[0];
    var cursory = pos[1];
    var start_col = Math.floor((cursorx-gamec.out_width) / gamec.margin);
    var start_row = Math.floor((cursory-gamec.out_width) / gamec.margin);
    if (((cursorx-gamec.out_width) % gamec.margin) > (gamec.margin/2)) {
        start_col++;
    }
    if (((cursory-gamec.out_width) % gamec.margin) > (gamec.margin/2)) {
        start_row++;
    }
    return [start_row, start_col]
}

function getCurPosition(e) {  
    var x, y; 
    if (e.pageX != undefined && e.pageY != undefined) {  
      x = e.pageX;
      y = e.pageY; 
    } else {  
      x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
      y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    }  
    x -= gamec.canvas.offsetLeft;
    y -= gamec.canvas.offsetTop;
    return [x, y];
} 

function canvasClickHandler(e){
	if(is_waiting){
	    return false;
	}
	var canvas = document.getElementById('game-canvas');
	var pos = getCurPosition(e);
	rowcol = getGridRowCol(pos);
	row = rowcol[0]
	col = rowcol[1]

	if(game_pieces[row][col] != 0){
	    return false;
	}
	gamemove(row, col);

} 
//哪一方该下棋的标记
function initStartSign(){
    $('#piece_sign_top').removeClass('gamemove-status');
    $('#piece_sign_bottom').removeClass('gamemove-status');
    var piece_signs = $('#piece_sign_top');
    if(my_piece == 1){
        piece_signs = $('#piece_sign_bottom');   
    }
    piece_signs.addClass('gamemove-status');
}

function sendchat(){
    var content = $('#chat-input').val();
    $('#chat-input').val('');            
    if (!content || room_status != 1) return;
    $('#chat-div ul').append('<li class="hischat-li"></li>');
    $('#chat-div ul li:last-child').text(content);
    $('#chat-div ul').scrollTop($('#chat-div ul')[0].scrollHeight);
    gamesocket.send(JSON.stringify({
        room: room_name,
        content: content,
        'type':'on_chat',
    }));
}

function gamemove(row, col){
    gamec.drawPiece(row, col, my_piece);
    gamesocket.send(JSON.stringify({
        room: room_name,
        row: row,
        col: col,
        'type':'on_gamemove',
    }));
    is_waiting = true;
    game_pieces[row][col] = my_piece;
    $('#game-canvas').css('cursor', 'default');
    $('#piece_sign_bottom').removeClass('gamemove-status');
    $('#piece_sign_top').addClass('gamemove-status');
}

/**
 * 对方上线
 * @param  {string} msg 
 * @return {bool}     
 */
function on_online(msg){

}
/**
 * 对方离线
 * @param  {string} msg 
 * @return {bool}     
 */
function on_offline(msg){
    is_waiting = true;
    room_status = 0;
    $('#status-span').text('对方离线');
    $('#game-canvas').css('cursor', 'default');
    $('#piece_sign_top').removeClass('gamemove-status');
    $('#piece_sign_bottom').removeClass('gamemove-status');
    $('#alert-title').text('对方离线');
     offline_timeout = setTimeout(function(){
       $('#alert-model-dom').data('id', 0).modal('show');
    }, 2000);
}
/**
 * 对方走一步棋
 * @param  {string} msg 
 * @return {bool}     
 */
function on_gamemove(msg){
    row = parseInt(msg.row);
    col = parseInt(msg.col);
    gamec.drawPiece(row, col, his_piece);
    game_pieces[row][col] = his_piece;
    $('#game-canvas').css('cursor', 'pointer');
    $('#piece_sign_top').removeClass('gamemove-status');
    $('#piece_sign_bottom').addClass('gamemove-status');
    is_waiting = false;
}
/**
 * 开始游戏
 * @param  {string} msg 
 * @return {bool}     
 */
function on_gamestart(msg){
    clearTimeout(offline_timeout);
    is_waiting = false;
    room_status = 1;
    $('#status-span').text('对方上线，游戏开始');
    gamec.canvas.width = gamec.canvas.width;
    gamec.drawGrid();
    $('#his_status_img').attr('src', status_imgs[his_piece-1]);
    $('#my_status_img').attr('src', status_imgs[my_piece-1]);
    if(my_piece == 1){  //黑先白后
        $('#game-canvas').css('cursor', 'pointer');
    }
    initStartSign();
}
/**
 * 游戏结束
 * @param  {string} msg 
 * @return {bool}     
 */
function on_gameover(msg){
    is_waiting = true;
    room_status = 2;
    $('#status-span').text('游戏结束');
    $('#piece_sign_top').removeClass('gamemove-status');
    $('#piece_sign_bottom').removeClass('gamemove-status');
    $('#game-canvas').css('cursor', 'default'); 
    pid = parseInt(msg.up)
    if (pid > 0 && pid != my_piece){
        row = parseInt(msg.row);
        col = parseInt(msg.col);
        gamec.drawPiece(row, col, his_piece);
        game_pieces[row][col] = his_piece;                  
    }
    $('#alert-title').text('游戏结束');
    $('#alert-model-dom').data('id', 0).modal('show');
}
/**
 * 聊天
 * @param  {string} msg 
 * @return {bool}     
 */
function on_chat(msg){
    $('#chat-div ul').append('<li class="hischat-li"></li>');
    $('#chat-div ul li:last-child').text(msg.content);            
    $('#chat-div ul').scrollTop($('#chat-div ul')[0].scrollHeight);
}

window.onbeforeunload = function () {
    gamesocket.close();
    // event.returnValue = "You will lose any unsaved content";
}

$(document).ready(function () {    
	for(i=0; i<=gamec.grid_count; i++){
        game_pieces[i] = new Array();
        for(j=0; j<=gamec.grid_count; j++){
            game_pieces[i][j] = 0;
        }
    }

    if(is_waiting ){
        $('#game-canvas').css('cursor', 'default');
    }
    if(room_status==0){
        $('#status-span').text('等待对方上线');
    }else{
        $('#status-span').text('游戏开始');
    }     

    gamec.canvas.addEventListener("click", canvasClickHandler, false);
    gamec.drawGrid();

    if(room_status != 0){
        initStartSign();
    }
  
    var WebSocket = window.WebSocket || window.MozWebSocket;
    if (WebSocket) {
        try {
            gamesocket = new WebSocket(wsurl);
        } catch (e) {
            alert(e)
        }
    }

    if (gamesocket) {
        gamesocket.onopen = function(){  
            //gamesocket.send(JSON.stringify({name:"yes"}));
        }  
        gamesocket.onmessage = function(event) {
            var msg = JSON.parse(event.data)
            switch(msg.type){
                case 'online':
                    on_online(msg);
                    break;
                case 'offline':
                    on_offline(msg);
                    break;
                case 'on_gamestart':
                    on_gamestart(msg);
                    break;
                case 'on_gamemove':
                    on_gamemove(msg);
                    break;
                case 'on_gameover':
                    on_gameover(msg);
                    break;
                case 'on_chat':
                    on_chat(msg);
                    break;
                default:
                    break;
            }
        }
    }
});
