# dual_mode.py

import asyncio

from venom import venom, Config, MyMessage, Collection
from venom.helpers import plugin_name


HELP_ = Config.HELP[plugin_name(__name__)] = {'type': 'essents', 'commands': []}


async def _init() -> None:
    found = await Collection.TOGGLES.find_one({'_id': 'USER_IS_SELF'})
    if found:
        Config.USER_IS_SELF = found['switch']
    else:
        Config.USER_IS_SELF = bool(Config.STRING_SESSION)

#######################################################################################################################################################

HELP_['commands'].append(
    {
        'command': 'mode',
        'flags': {
            '-c': 'check',
        },
        'usage': 'toggle mode [user/bot]',
        'syntax': '{tr}mode [optional flag]',
        'sudo': False
    }
)

@venom.trigger('mode')
async def dual_mode(_, message: MyMessage):
    " toggle mode [user/bot] "
    if '-c' in message.flags:
        switch_ = "USER" if Config.USER_IS_SELF else "BOT"
        return await message.edit(f"Current mode: <b>{switch_}</b>.", del_in=5)
    if not Config.STRING_SESSION:
        return await message.edit("`Can't change to USER mode without STRING_SESSION.`", del_in=3)
    if Config.USER_IS_SELF:
        Config.USER_IS_SELF = False
        mode_ = "BOT"
    else:
        Config.USER_IS_SELF = True
        mode_ = "USER"
    await asyncio.gather(
        Collection.TOGGLES.update_one(
            {'_id': 'USER_IS_SELF'}, {'$set': {'switch': Config.USER_IS_SELF}}, upsert=True
        ),
        message.edit(f"Mode changed to: <b>{mode_}</b>.", del_in=7)
    )