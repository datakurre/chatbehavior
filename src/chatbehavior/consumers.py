# -*- coding: utf-8 -*-
""" Consumers """

import re
import random
import datetime
import simplejson

from five import grok

from zope.interface import Interface
from zope.component import getUtility

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName

from collective.zamqp.consumer import Consumer
from collective.zamqp.interfaces import (
    IMessageArrivedEvent,
    IProducer
)

from chatbehavior.interfaces import IChat


class IChatMessage(Interface):
    """ Chat message marker interface """


class ChatConsumer(Consumer):
    """ Chat consumer """
    grok.name("chatbehavior.${site_id}")

    connection_id = "chat"
    durable = False
    marker = IChatMessage


@grok.subscribe(IChatMessage, IMessageArrivedEvent)
def consumeMessage(message, event):

    exchange = message.method_frame.exchange
    correlation_id = message.header_frame.correlation_id
    uuid = re.sub("^messages-", "", exchange or "")
    obj = None

    if uuid:
        site = getUtility(ISiteRoot)
        pc = getToolByName(site, "portal_catalog")
        brains = pc.unrestrictedSearchResults(UID=uuid)
        if brains:
            obj = brains[0]._unrestrictedGetObject()

    # Note: for published object, it would be enough to just
    # obj = uuid and uuidToObject(uuid) or None

    if obj:
        chat = IChat(obj)

        saved_message = {
            "sent": datetime.datetime.now(),
            "from": message.body.get("from"),
            "body": message.body.get("body"),
        }

        inserted = 0
        while not inserted:
            intid = random.randint(0, 2 ** 31 - 1)
            inserted = chat.messages.insert(intid, saved_message)
        chat.index.index_doc(intid, saved_message["sent"])

    if obj and correlation_id:
        producer = getUtility(IProducer, name="chat")
        producer.register()  # register for the current transaction
        confirmed_message = {
            "sent": saved_message["sent"].strftime("%s"),
            "from": saved_message["from"],
            "body": saved_message["body"]
        }
        producer.send(
            simplejson.dumps(confirmed_message),
            content_type="application/x-json",
            exchange="confirms-%s" % uuid,
            routing_key="*",
            correlation_id=correlation_id
        )

    message.ack()
