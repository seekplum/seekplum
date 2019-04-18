/**
 * Created by Administrator on 2017/2/11.
 */
$(document).ready(function () {
    var uuid = $('#uuid').val();
    var host = $('#host').val();


    /**
     * 0.1 秒后启动websocket
     * */
    setTimeout(function () {
        book_websocket(host, uuid);
    }, 100);


    /**
     * 购买书籍
     * */
    $('#add-button').click(function (event) {
        jQuery.ajax({
            url: '/cart',
            type: 'POST',
            data: {
                uuid: uuid,
                action: 'add'
            },
            dataType: 'json',
            success: function (data) {
                if (data['code'] != 0&& data["uuid"] == uuid) {
                    $('#message').html(data['message']);
                }
                else {
                    $('#message').html("");
                }
            }
        });
    });

    /**
     * 移除书籍
     * */
    $('#remove-button').click(function (event) {
        jQuery.ajax({
            url: '/cart',
            type: 'POST',
            data: {
                uuid: uuid,
                action: 'remove'
            },
            dataType: 'json',
            beforeSend: function (xhr, settings) {
            },
            success: function (data, status, xhr) {
                if (data['code'] != 0&& data["uuid"] == uuid) {
                    $('#message').html(data['message']);
                }
                else {
                    $('#message').html("");
                }
            }
        });
    });
});

/**
 * Websocket
 * */
function book_websocket(host, uuid) {
    var websocket = new WebSocket(host);
    websocket.onopen = function (evt) {
        // 打开文本socket
        console.log("web socket 连接开始: " + uuid);
        var data = {"uuid": uuid};
        // 发送消息给后端
        websocket.send(JSON.stringify(data));
    };
    websocket.onmessage = function (evt) {
        var data = JSON.parse(evt.data);
        // 接收后端的消息
        console.log("当前页面uuid: " + uuid + " 收到消息的uuid: " + data.uuid);
        if (data.uuid == uuid) {
            console.log("总数量:" + data.count + "购买数量:" + data.curr_count);
            $('#curr_count').html(data.curr_count);
        }
        // 修改总数量
        $('#count').html(data.count);
    };
    websocket.onerror = function (evt) {
    };
    websocket.onclose = function (evt) {
        // 关闭websocket
        console.log("web socket 连接关闭");
    }
}