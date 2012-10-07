# IMPORTANT! To make the stomp connections safe, you must make sure that
# the guest user on RabbitMQ has minimal permissions, including
#
# Configure     Write                     Read
# 'amq.gen-.*', 'amq.gen-.*|messages-.*', 'amq.gen-.*|messages-.*|confirms-.*'

jQuery ($) ->
  # GUID-like random id generator is used to identify each live-message.
  GUID = ->
    S4 = -> Math.floor(Math.random() * 0x10000).toString(16)
    "#{S4()}#{S4()}-#{S4()}-#{S4()}-#{S4()}-#{S4()}#{S4()}#{S4()}"

  # Then we, reset a dummy list to contain all GUIDs of the messages that
  # we have sent ourselves.
  my_messages = []

  # And then we are ready to find the chat placeholder on the page and
  # make it alive!
  $("#viewlet-above-content-body .chat").each ->
    chat = $(this)

    # Exchanges to send and receive messaged and receive confirmation for
    # saved messages are being read from data-attributes.
    messages = chat.data("messages")
    confirms = chat.data("confirms")

    # A simple message template is used to render ne messages later on.
    message_template = '<p class="chatMessage">' +
                          '<span class="chatMessageSent"/>' +
                          '<span class="chatMessageFrom"/>' +
                          '<span class="chatMessageBody"/>' +
                        '</p>'

    # Message input takes the message body and creates a STOMP message
    # out of it.
    message_input = $('<input name="message" type="text" size="60" ' +
                      'placeholder="Type your message here and press enter" ' +
                      '/>')
    $(message_input).keyup((event) -> if event.keyCode == 13
      if $(this).val().trim()
        msg = JSON.stringify
          sent: (Number(new Date()) / 1000).toString()
          from: $(this).prev("input").val()
          body: $(this).val().trim()
        headers =
          "content-type": "application/x-json"
          "routing-key": "*"
          "correlation-id": GUID()
        client.send "/exchange/#{messages}/", headers, msg
        my_messages.push(headers["correlation-id"])
        $(this).val("")
    ).prependTo(chat)

    # Nick input field allows you to set a username for yourself.
    nick_input = $('<input name="nick" type="text" size="16" ' +
                   'placeholder="Your nick" />')
    $(nick_input).prependTo(chat)

    on_connect_guest = (response) ->
      console?.log "on_connect #{response}"

      # We subscribe to receive all the messages and render them.
      client.subscribe "/exchange/#{messages}", (message) ->
        console?.log message

        data = JSON.parse(message.body)

        sent = new Date(parseInt(data.sent) * 1000)
        sent = "#{sent.getFullYear()}-" +
               "#{sent.getMonth() < 9 and '0' or ''}#{sent.getMonth() + 1}-" +
               "#{sent.getDate() < 10 and '0' or ''}#{sent.getDate()} " +
               "#{sent.getHours() < 10 and '0' or ''}#{sent.getHours()}:" +
               "#{sent.getMinutes() < 10 and '0' or ''}#{sent.getMinutes()}"

        message_p = $(message_template)
          .find('.chatMessageSent').text(sent).end()
          .find('.chatMessageFrom').text(data.from).end()
          .find('.chatMessageBody').text(data.body).end()
          .addClass("chatPendingMessage")
          .attr("id", message.headers["correlation-id"])

        if message_p.attr("id") in my_messages
          message_p.addClass("chatMyMessage")
        chat.find("input:last").after(message_p)

      # We also subscribe to receive confirmations that messages have been
      # persisted onto our Plone-site.
      client.subscribe "/exchange/#{confirms}", (message) ->
        console?.log message
        $("##{message.headers['correlation-id']}")
          .removeClass("chatPendingMessage")

    on_error_guest = (response) ->
      console?.log "on_error #{response}"

    connect_guest = ->
      client.connect "guest", "guest", on_connect_guest, on_error_guest, "/"

    # Now everything is defined and we are ready for action:
    #
    # 1) Let's configure our stomp library to use SockJS
    Stomp.WebSocketClass = SockJS

    # 2) And create a new stomp client ready to open a connction
    client = Stomp.client "http://" + window.location.hostname + ":55674/stomp"

    # 3) Connect!
    do connect_guest
