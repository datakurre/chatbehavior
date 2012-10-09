// Generated by CoffeeScript 1.3.3
(function() {
  var __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  jQuery(function($) {
    var GUID, my_messages;
    GUID = function() {
      var S4;
      S4 = function() {
        return Math.floor(Math.random() * 0x10000).toString(16);
      };
      return "" + (S4()) + (S4()) + "-" + (S4()) + "-" + (S4()) + "-" + (S4()) + "-" + (S4()) + (S4()) + (S4());
    };
    my_messages = [];
    return $("#viewlet-below-content-body .chat").each(function() {
      var chat, client, confirms, connect_guest, message_input, message_template, messages, nick_input, on_connect_guest, on_error_guest;
      chat = $(this);
      messages = chat.data("messages");
      confirms = chat.data("confirms");
      message_template = '<p class="chatMessage">' + '<span class="chatMessageSent"/>' + '<span class="chatMessageFrom"/>' + '<span class="chatMessageBody"/>' + '</p>';
      message_input = $('<input name="message" type="text" size="60" ' + 'placeholder="Type your message here and press enter" ' + '/>');
      $(message_input).keyup(function(event) {
        var headers, msg;
        if (event.keyCode === 13) {
          if ($(this).val().trim()) {
            msg = JSON.stringify({
              sent: (Number(new Date()) / 1000).toString(),
              from: $(this).prev("input").val(),
              body: $(this).val().trim()
            });
            headers = {
              "content-type": "application/x-json",
              "correlation-id": GUID()
            };
            client.send("/exchange/" + messages + "/*", headers, msg);
            my_messages.push(headers["correlation-id"]);
            return $(this).val("");
          }
        }
      }).prependTo(chat);
      nick_input = $('<input name="nick" type="text" size="16" ' + 'placeholder="Your nick" />');
      $(nick_input).prependTo(chat);
      on_connect_guest = function(response) {
        if (typeof console !== "undefined" && console !== null) {
          console.log("on_connect " + response);
        }
        client.subscribe("/exchange/" + messages, function(message) {
          var data, message_p, sent, _ref;
          if (typeof console !== "undefined" && console !== null) {
            console.log(message);
          }
          data = JSON.parse(message.body);
          sent = new Date(parseInt(data.sent) * 1000);
          sent = ("" + (sent.getFullYear()) + "-") + ("" + (sent.getMonth() < 9 && '0' || '') + (sent.getMonth() + 1) + "-") + ("" + (sent.getDate() < 10 && '0' || '') + (sent.getDate()) + " ") + ("" + (sent.getHours() < 10 && '0' || '') + (sent.getHours()) + ":") + ("" + (sent.getMinutes() < 10 && '0' || '') + (sent.getMinutes()));
          message_p = $(message_template).find('.chatMessageSent').text(sent).end().find('.chatMessageFrom').text(data.from).end().find('.chatMessageBody').text(data.body).end().addClass("chatPendingMessage").attr("id", message.headers["correlation-id"]);
          if (_ref = message_p.attr("id"), __indexOf.call(my_messages, _ref) >= 0) {
            message_p.addClass("chatMyMessage");
          }
          return chat.find("input:last").after(message_p);
        });
        return client.subscribe("/exchange/" + confirms, function(message) {
          if (typeof console !== "undefined" && console !== null) {
            console.log(message);
          }
          return $("#" + message.headers['correlation-id']).removeClass("chatPendingMessage");
        });
      };
      on_error_guest = function(response) {
        return typeof console !== "undefined" && console !== null ? console.log("on_error " + response) : void 0;
      };
      connect_guest = function() {
        return client.connect("guest", "guest", on_connect_guest, on_error_guest, "/");
      };
      Stomp.WebSocketClass = SockJS;
      client = Stomp.client("http://" + window.location.hostname + ":55674/stomp");
      return connect_guest();
    });
  });

}).call(this);
