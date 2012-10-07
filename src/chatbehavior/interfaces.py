# -*- coding: utf-8 -*-
""" Interfaces """

from zope.interface import (
    Interface,
    Attribute,
)


class IChat(Interface):
    """ Chat for Dexterity content type """

    messages = Attribute("Chat messages")


class IChattable(Interface):
    """ Marker interface for chattable content """

