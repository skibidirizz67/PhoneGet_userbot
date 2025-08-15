import json, re, os
import asyncio
import consts as c
import matplotlib.pyplot as plt
import numpy as np

async def get_phones(client, logging):
    phones_list = {}

    try:
        async with client.conversation(c.target_id, timeout=10) as conv:
            await conv.send_message(c.cmds['ps'])
            resp = await conv.get_response()
            for i in range(0, 8):
                logging.info(f'rarity {i}')
                phones_list[i] = {}
                if i == 6:
                    await conv.send_message(c.cmds['av'])
                    resp = await conv.get_response()
                    await resp.click(5, 0)
                    resp = await conv.get_edit()
                    await resp.click(1, 0)
                    resp = await conv.get_edit()
                if i > 5: await resp.click(i, 0)
                else: await resp.click(int(i/2), i%2)
                resp = await conv.get_edit()
                match_ = re.search(r'(\d+)$', resp.buttons[5][0 if i > 5 else 1].text)
                if not match_: match_ = re.search(r'(\d+)', '1')
                for p in range(int(match_.group(1))):
                    logging.info(f'page {p}')
                    for j in range(5):
                        if '⬅️' in resp.buttons[j][0].text: break
                        match_ = re.search(r'^(.+)\s\((\d+)', resp.buttons[j][0].text)
                        if not match_: match_ = re.search(r'(.*)()?()?', resp.buttons[j][0].text)
                        phones_list[i].update({match_.group(1): int(match_.group(2)) if match_.group(2) else 0})
                    if len(resp.buttons[len(resp.buttons)-2]) > 2 and '➡️' in resp.buttons[len(resp.buttons)-2][2].text: await resp.click(len(resp.buttons)-2, 2)
                    elif i == 6 and p == 0: await resp.click(len(resp.buttons)-2, 1)
                    else: break
                    resp = await conv.get_edit()
                    await asyncio.sleep(0.5)
                await resp.click(len(resp.buttons)-1, 0)
                resp = await conv.get_edit()
    except TimeoutError:
        logging.error('timeout')
    logging.info('done')


    for key in phones_list[6]: phones_list[6][key] = 500000
    for key in phones_list[7]: phones_list[7][key] = 3000000
    
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phones_list.json'), 'w') as f:
        json.dump(phones_list, f, indent=4)
