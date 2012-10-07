# -*- coding: utf-8 -*-
""" Behaviors """

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
from plone.app.layout.viewlets.interfaces import IAboveContentBody
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

    grok.viewletmanager(IAboveContentBody)
    grok.context(IChattable)
    grok.require("zope2.View")

    def update(self):
        site = getUtility(ISiteRoot)
        site_id = site.getId()

        # Configure channel and bind our consumer to listen to it
        with BlockingChannel("chat") as channel:
            channel.exchange_declare(
                exchange="messages-%s" % self.getUUID(),
                auto_delete=True, type="fanout"
            )
            channel.exchange_declare(
                exchange="confirms-%s" % self.getUUID(),
                auto_delete=True, type="fanout"
            )
            channel.queue_bind(
                queue="chatbehavior.%s" % site_id,
                exchange="messages-%s" % self.getUUID()
            )

        chat = IChat(self.context)

        created = self.context.created().asdatetime()
        start = getattr(self.context, "_v_chat_last_lookup",
                        datetime.datetime(*created.timetuple()[:6]))
        end = datetime.datetime.now()
        setattr(self.context, "_v_chat_last_lookup", end)

        lookup = (chat.messages[idx] for idx in chat.index.apply((start, end)))
        messages = sorted(lookup, cmp=lambda x, y: cmp(y["sent"], x["sent"]))

        all_messages = getattr(self.context, "_v_chat_messages", [])
        messages.extend(all_messages)
        setattr(self.context, "_v_chat_messages", messages)

        self.messages = messages

    def getUUID(self):
        return IUUID(self.context)
