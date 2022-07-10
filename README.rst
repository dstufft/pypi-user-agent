pypi-user-agent
===============

Reusable utility for creating a user-agent that PyPI can interpret
and publish statistics into it's BigQuery database using.


Installation
------------

Use ``pip`` to install::

    pip install pypi-user-agent


Usage
-----

This library offers only a single function, ``user_agent``, which
takes two mandatory parameters (``name`` and ``version``) and one
optional parameter (``user_data``).


.. code-block:: python

    import os
    from pypi_user_agent import user_agent

    ua = user_agent("pip", "22.0", user_data=os.environ.get("PIP_USER_AGENT_USER_DATA"))

This function returns a str which you should use as your UserAgent
when downloading from PyPI or fetching responses from the simple
repository API.

.. note::
    Simply setting your user-agent isn't enough to have data show up in
    BigQuery, you also need to update `linehual <https://github.com/pypa/linehaul-cloud-function/>`_
    to know to parse your user-agent in this format.


Code of Conduct
---------------

Everyone interacting in the packaging project's codebases, issue trackers, chat
rooms, and mailing lists is expected to follow the `PSF Code of Conduct`_.

.. _PSF Code of Conduct: https://github.com/pypa/.github/blob/main/CODE_OF_CONDUCT.md
