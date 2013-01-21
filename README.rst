This is NOT an example on how to implement chat behavior for Plone content.
This is just a demo on how AMQP (and message queues in general) can be used to
serialize write operations for ZODB.

::

    python bootstrap.py
    bin/buildout

    source bin/rabbitmq-env
    bin/supervisord
