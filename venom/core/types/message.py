# message.py

import os
import re
from typing import List, Union, Dict

from pyrogram import filters as flt, Client
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import (MessageAuthorRequired, MessageDeleteForbidden,
                             MessageIdInvalid, MessageTooLong, MessageNotModified)
from pyrogram.types import InlineKeyboardMarkup, Message

import venom
from venom import Config
from .. import client as _client

_CANCEL_PROCESS: List[int] = []


class MyMessage(Message):

    def __init__(self,
                 client: Union['_client.Venom', '_client.VenomBot', Client],
                 mvars: Dict[str, object],
                 **kwargs: Union[str, bool]) -> None:
        """ Modified Message """
        self._flags = {}
        self._filtered_input = ""
        self._kwargs = kwargs
        self.venom_client = client
        super().__init__(client=client, **mvars)

    @classmethod
    def parse(cls, client: Union['_client.Venom', '_client.VenomBot'], message: Message, **kwargs):
        if not message:
            return
        vars_ = vars(message)
        for one in ['_client', '_flags', '_filtered_input', '_kwargs', 'venom_client']:
            if one in vars_:
                del vars_[one]
        if vars_['reply_to_message']:
            vars_['reply_to_message'] = cls.parse(client, vars_['reply_to_message'], **kwargs)
        return cls(client, vars_, **kwargs)

    @property
    def client(self) -> Client | None:
        """ return client """
        return self._client

    @property
    def replied(self) -> Union['MyMessage', None]:
        if not hasattr(self, 'reply_to_message'):
            return None
        replied_msg = self.reply_to_message
        return self.parse(self.venom_client, replied_msg)

    @property
    def input_str(self) -> str:
        if not self.text:
            return ""
        if " " in self.text or "\n" in self.text:
            text_ = self.text
            split_ = text_.split(maxsplit=1)
            input_ = split_[-1]
            return input_
        return ''

    @property
    def flags(self) -> list:
        input_ = self.input_str
        if not input_:
            return []
        flags_ = []
        line_num = 0
        while True:
            first_line = input_.splitlines()[line_num]
            if first_line:
                break
            else:
                line_num += 1
        str_ = first_line.split()
        for one in str_:
            match = re.search(r"^(-[a-z]+)(\d.*)?$", one)
            if not hasattr(match, 'group'):
                break
            if match.group(2):
                flags_.append({
                    str(match.group(1)): int(match.group(2))
                })
            elif match.group(1):
                flags_.append(str(match.group(1)))
        return flags_

    @property
    def filtered_input(self) -> str:
        """ filter flags out and return string """
        input_ = self.input_str
        if not input_:
            return ""
        flags = self.flags
        for one in flags:
            if isinstance(one, dict):
                key_ = one.keys()[0]
                one = f"{key_}{one[key_]}"
            input_ = input_.lstrip(one).strip()
        return input_

    @property
    def process_is_cancelled(self) -> bool:
        """ check if process is cancelled """
        if self.id in _CANCEL_PROCESS:
            _CANCEL_PROCESS.remove(self.id)
            return True
        return False

    def cancel_process(self) -> None:
        """ cancel process """
        _CANCEL_PROCESS.append(self.id)

    async def send_as_file(self,
                           text: str,
                           file_name: str = 'output.txt',
                           caption: str = '',
                           delete_message: bool = True,
                           reply_to: int = None) -> 'MyMessage':
        """ send text as file """
        file_ = os.path.join(Config.TEMP_PATH, file_name)
        with open(file_, "w+", encoding='utf-8') as fn:
            fn.write(str(text))
        if delete_message:
            try:
                await self.delete()
            except MessageDeleteForbidden:
                pass
        if reply_to:
            reply_to_id = reply_to
        else:
            reply_to_id = self.id if not self.reply_to_message else self.reply_to_message.id
        message = await self._client.send_document(chat_id=self.chat.id,
                                                   document=file_,
                                                   file_name=file_name,
                                                   caption=caption,
                                                   reply_to_message_id=reply_to_id)
        os.remove(file_)
        return self.parse(self.venom_client, message)

    async def edit(self,
                   text: str,
                   dis_preview: bool = False,
                   del_in: int = -1,
                   parse_mode: ParseMode = ParseMode.DEFAULT,
                   reply_markup: InlineKeyboardMarkup = None,
                   sudo: bool = True,
                   **kwargs) -> 'MyMessage':
        """ edit or reply message """
        # if self.reactions is not None and self.reactions != []:
        #     return
        reply_to_id = self.replied.id if self.replied else self.id
        try:
            message = await self._client.edit_message_text(
                chat_id=self.chat.id,
                message_id=self.id,
                text=text,
                del_in=del_in,
                parse_mode=parse_mode,
                dis_preview=dis_preview,
                reply_markup=reply_markup,
                **kwargs
            )
            return self.parse(self.venom_client, message)
        except MessageNotModified:
            return self
        except (MessageAuthorRequired, MessageIdInvalid) as msg_err:
            if sudo:
                reply_ = await self._client.send_message(chat_id=self.chat.id,
                                                         text=text,
                                                         del_in=del_in,
                                                         dis_preview=dis_preview,
                                                         parse_mode=parse_mode,
                                                         reply_markup=reply_markup,
                                                         reply_to_message_id=reply_to_id,
                                                         **kwargs)
                parsed = self.parse(self.venom_client, reply_)
                self.old_message = self
                self.id = parsed.id
                return parsed
            raise msg_err

    edit_text = try_to_edit = edit

    async def err(self, text: str):
        """ Method for showing errors """
        format_ = f"<b>Error</b>:\n{text}"
        try:
            return await self.edit(text)
        except Exception as e:
            venom.test_print(e)

    async def reply(self,
                    text: str,
                    dis_preview: bool = False,
                    del_in: int = -1,
                    parse_mode: ParseMode = ParseMode.DEFAULT,
                    reply_markup: InlineKeyboardMarkup = None,
                    quote: bool = True,
                    **kwargs) -> 'MyMessage':
        """ reply message """

        reply_to_id = self.replied.id if (quote and self.replied) else None

        reply_ = await self._client.send_message(chat_id=self.chat.id,
                                                 text=text,
                                                 del_in=del_in,
                                                 dis_preview=dis_preview,
                                                 parse_mode=parse_mode,
                                                 reply_to_message_id=reply_to_id,
                                                 reply_markup=reply_markup,
                                                 **kwargs)
        return reply_ if self.chat.type != ChatType.PRIVATE else self.parse(self, reply_)

    async def edit_or_send_as_file(self,
                                   text: str,
                                   file_name: str = "File.txt",
                                   caption: str = None,
                                   del_in: int = -1,
                                   parse_mode: ParseMode = ParseMode.DEFAULT,
                                   dis_preview: bool = False,
                                   **kwargs) -> 'MyMessage':
        """ edit or send as file """
        try:
            return await self.edit(
                text=text,
                del_in=del_in,
                parse_mode=parse_mode,
                dis_preview=dis_preview,
                **kwargs
            )
        except MessageTooLong:
            reply_to = self.replied.id if self.replied else self.id
            msg_ = await self.send_as_file(text=text,
                                           file_name=file_name,
                                           caption=caption,
                                           reply_to=reply_to)
            return msg_

    async def reply_or_send_as_file(self,
                                    text: str,
                                    file_name: str = "File.txt",
                                    caption: str = None,
                                    del_in: int = -1,
                                    parse_mode: ParseMode = ParseMode.DEFAULT,
                                    dis_preview: bool = False) -> 'MyMessage':
        """ reply or send as file """
        try:
            return await self.reply(text=text, del_in=del_in, parse_mode=parse_mode, dis_preview=dis_preview)
        except MessageTooLong:
            reply_to = self.replied.id if self.replied else self.id
            msg_ = await self.send_as_file(text=text,
                                           file_name=file_name,
                                           caption=caption,
                                           reply_to=reply_to)
            os.remove(file_name)
            return msg_

    async def delete(self, revoke: bool = True) -> bool:
        """ message delete method """
        try:
            await self.delete()
            return True
        except MessageAuthorRequired:
            return False

    async def ask(self, text: str, timeout: int = 15, filters: flt.Filter = None) -> 'MyMessage':
        """ monkey patching to MyMessage using pyromod.ask """
        return await self.venom_client.ask(chat_id=self.chat.id, text=text, timeout=timeout, filters=filters)

    async def wait(self, timeout: int = 15, filters: flt.Filter = None) -> 'MyMessage':
        """ monkey patching to MyMessage using pyromod's listen """
        return await self.venom_client.listen(self.chat.id, timeout=timeout, filters=filters)
