# -*- coding: utf-8 -*-
""" Behaviors """

import socket
import datetime

from BTrees.IOBTree import IOBTree

from five import grok

from zope.interface import implements

from zope.component import (
    adapts,
    getUtility
)

from zope.index.field import FieldIndex

from zope.annotation.interfaces import IAnnotations

from Products.CMFCore.interfaces import ISiteRoot

from plone.uuid.interfaces import IUUID
from plone.app.layout.viewlets.interfaces import IBelowContentBody
from plone.dexterity.interfaces import IDexterityContent

from collective.zamqp.connection import BlockingChannel

from chatbehavior.interfaces import (
    IChat,
    IChattable
)


class Chat(object):
    """ Chat storage adapter for Dexterity content """

    implements(IChat)
    adapts(IDexterityContent)

    def __init__(self, context):
        self.context = context
        annotations = IAnnotations(context)

        if not "chatbehavior.messages" in annotations:
            annotations["chatbehavior.messages"] = IOBTree()

        if not "chatbehavior.index" in annotations:
            annotations["chatbehavior.index"] = FieldIndex()

        self.index = annotations["chatbehavior.index"]
        self.messages = annotations["chatbehavior.messages"]


class ChatViewlet(grok.Viewlet):
    """ Chat viewlet """

    grok.viewletmanager(IBelowContentBody)
    grok.context(IChattable)
    grok.require("zope2.View")
    grok.name("chatviewlet")

    def update(self):
        # Before we can prepare the chat viewlet, we must ensure that
        # chat-specific AMQP-exchanges have been declared:
        site = getUtility(ISiteRoot)
        ensureExchangesAndBindings(self.getUUID(), site.getId())
        #

        chat = IChat(self.context)

        created = self.context.created().asdatetime()
        start = getattr(self.context, "_v_chat_last_lookup",
                        datetime.datetime(*created.timetuple()[:6]))
        end = datetime.datetime.now()
        setattr(self.context, "_v_chat_last_lookup", end)

        lookup = chat.index.apply((start, end))
        messages = [chat.messages[idx] for idx in
                    chat.index.sort(lookup, reverse=True)]

        all_messages = getattr(self.context, "_v_chat_messages", [])
        messages.extend(all_messages)
        setattr(self.context, "_v_chat_messages", messages)

        self.messages = messages

    def getUUID(self):
        return IUUID(self.context)


def ensureExchangesAndBindings(uuid, site_id):
    # Before we can prepare the chat viewlet, we must ensure that
    # chat-specific AMQP-exchanges have been declared:
    try:
        with BlockingChannel("chat") as channel:
            channel.exchange_declare(
                exchange="messages-%s" % uuid,
                auto_delete=True, type="fanout"
            )
            # Confirms-exchanges cannot be auto deleted, because browsers may
            # close their connections becore we have confirmed their messages
            # (and auto-deleting would delete the exchange too early.)
            channel.exchange_declare(
                exchange="confirms-%s" % uuid,
                auto_delete=False, type="fanout"
            )
            channel.queue_bind(
                queue="chatbehavior.%s" % site_id,
                exchange="messages-%s" % uuid
            )
    except socket.timeout:
        # Try again until maximum recursion depth is exceeded. Well,
        # there's 1s socket timeout in Pika's BlockingConnection and
        # that may happen on slow VServer used in our demo.
        ensureExchangesAndBindings(uuid, site_id)
