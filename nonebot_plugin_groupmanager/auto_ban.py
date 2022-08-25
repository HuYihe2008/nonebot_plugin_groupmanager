# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/1/29 0:43
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : auto_ban.py
# @Software: PyCharm
import os
import re
from os import path

from httpx import AsyncClient
from nonebot import logger, on_message, on_command, require
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

from .config import plugin_config
from .path import *
from .utils import banSb, load, get_user_violation, log_sd, fi

cron_update = plugin_config.cron_update
paths_ = [config_path, limit_word_path, limit_word_path_easy, limit_level]

f_word = on_message(priority = 2, block = False)


@f_word.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    '''
    违禁词禁言
    :param bot:
    :param event:
    :return:
    '''
    gid = event.group_id
    level = await load(limit_level)
    if os.path.exists(limit_word_path_custom / f"{gid}.txt"):  # 是否存在自定义违禁词
        with open(limit_word_path_custom / f"{gid}.txt", 'r', encoding = 'utf-8') as f:
            custom_limit_words = await f.read()
    else:
        custom_limit_words = ''
    if str(gid) in level:
        limit_path = limit_word_path_easy if level[str(gid)] == 'easy' else limit_word_path
        rules = [re.sub(r'\t+', '\t', rule).split('\t') for rule in
                 (open(limit_path, 'r', encoding = 'utf-8').read() + custom_limit_words).split('\n')]
        msg = re.sub(r'\s', '', str(event.get_message()))
        logger.info(f"{gid}收到{event.user_id}的消息: \"{msg}\"")
        for rule in rules:
            if rule[0] and re.search(rule[0], msg):
                level = (await get_user_violation(gid, event.user_id, 'Porn', event.raw_message))
                ts: list = time_scop_map[level]
                await log_sd(f_word, f"你发送了违禁词,现在进行处罚,如有异议请联系管理员\n你的违禁级别为{level}级", f"敏感词触发: \"{rule[0]}\"", True)
                matcher.stop_propagation()  # block
                delete, ban = True, True
                if len(rule) > 1:
                    delete = rule[1].find('$撤回') != -1
                    ban = rule[1].find('$禁言') != -1
                if delete:
                    try:
                        await bot.delete_msg(message_id = event.message_id)
                        logger.info('消息已撤回')
                    except ActionFailed:
                        logger.info('消息撤回失败')
                if ban:
                    baning = banSb(gid, ban_list = [event.get_user_id()], scope = ts)
                    async for baned in baning:
                        if baned:
                            try:
                                await baned
                                await log_sd(f_word, f"你发送了违禁词,现在进行处罚,如有异议请联系管理员\n你的违禁级别为{level}级", f"禁言成功，用户: {uid}", True)
                            except ActionFailed:
                                await log_sd(f_word, '禁言失败，权限不足')
                break
        
    await fi(f_word, '本群未配置检测级别，指令如下：\n1.简单违禁词:简单级别\n2.严格违禁词：严格级别\n3.群管初始化：一键配置所有群聊为简单级别\n若重复出现此信息推荐发送【简单违禁词】')


if cron_update:
    async def auto_upload_f_words():
        logger.info('自动更新严格违禁词库...')
        async with AsyncClient() as client:
            try:
                r = (await client.get(url = 'https://fastly.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_s')).text
            except Exception as err:
                logger.error(f"自动更新严格违禁词库失败：{err}")
                return True
        with open(limit_word_path, 'w', encoding = 'utf-8') as f:
            f.write(r)
        logger.info('正在更新简单违禁词库')
        async with AsyncClient() as client:
            try:
                r = (await client.get(url = 'https://fastly.jsdelivr.net/gh/yzyyz1387/nwafu/f_words/f_word_easy')).text
            except Exception as err:
                logger.error(f"自动更新简单违禁词库失败：{err}")
                return True
        with open(limit_word_path_easy, 'w', encoding = 'utf-8') as f:
            f.write(r)
        logger.info('更新完成')


    scheduler = require('nonebot_plugin_apscheduler').scheduler
    # 每周一更新违禁词库
    scheduler.add_job(auto_upload_f_words, 'cron', day_of_week = 'mon', hour = 0, minute = 0, second = 0,
                      id = 'auto_upload_f_words')

    update_f_words = on_command('更新违禁词库', priority = 1, permission = GROUP_ADMIN | GROUP_OWNER | SUPERUSER)


    @update_f_words.handle()
    async def _(bot: Bot):
        upload_ = await auto_upload_f_words()
        await fi(update_f_words, '更新时出现错误' if upload_ else '更新成功')
