# listen.py
import inspect
from typing import Union

import pyromod.listen
from pyrogram import Client as RClient
from pyrogram import filters as flt

from ... import client as _client
from ... import types


class Listen(RClient):

    async def listen(self,
                     chat_id: Union[str, int],
                     timeout: int = 15,
                     filters: flt.Filter = None,
                     **kwargs) -> 'types.message.MyMessage':
        """ custom listener for VenomX """
        msg = await super().listen(chat_id=chat_id, timeout=timeout, filters=filters, **kwargs)

        client_ = _client.Venom.parse(self)
        # module = inspect.currentframe().f_back.f_globals['__name__']

        return types.message.MyMessage.parse(client_, msg)

    async def ask(self,
                  text: str,
                  chat_id: Union[str, int],
                  timeout: int = 15,
                  filters: flt.Filter = None,
                  **kwargs) -> 'types.message.MyMessage':
        """ custom ask for VenomX """

        msg = await super().ask(chat_id=chat_id,
                                text=text,
                                timeout=timeout,
                                filters=filters,
                                **kwargs)

        client_ = _client.Venom.parse(self)
        # module = inspect.currentframe().f_back.f_globals['__name__']

        return types.message.MyMessage.parse(client_, msg)
