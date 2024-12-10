import requests
import asyncio
import config
import os
import traceback
import logging
import aiohttp
from twitchio.ext import commands

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

if(os.path.exists('config.cfg')):
    logging.info('Loading config')
    cfg = config.Config('config.cfg')
else:
    logging.error("Error. I don't see a file named config.cfg, is it in the same folder as the bot? Exiting")
    exit(1)

async def lookupSquadServer(bmPlayerID, channel):
    try:

        battleMetricsKey = {'Authorization': 'Bearer ' + cfg['BmAPIkey']}
        
        async with aiohttp.ClientSession(headers=battleMetricsKey) as session:
            async with session.get('https://api.battlemetrics.com/players/'+str(bmPlayerID)+'/relationships/sessions') as response:
                bmSessionData = (await response.json())['data']
            for session in bmSessionData:
                if (session['type'] != 'session'):
                    continue
                if (session['attributes']['stop'] == None):
                    currentServerBMID = session['relationships']['server']['data']['id']
                    break
        async with aiohttp.ClientSession(headers=battleMetricsKey) as session:
            async with session.get('https://api.battlemetrics.com/servers/' + str(currentServerBMID)) as response:
                serverInfo = (await response.json())
            serverName = serverInfo['data']['attributes']['name']
            queue = "N/A"
            try:
                queue = serverInfo['data']['attributes']['details']['squad_publicQueue']
            except:pass
            map1 = serverInfo['data']['attributes']['details']['map']

        return channel + " is currently on: " + serverName + " -- The queue is " + str(queue) + ". Currently playing layer: " + str(map1)
    except Exception as e:
        logging.error(f"Error looking up squad server: {e}\n{traceback.format_exc()}")
        return channel + " is currently not on a Squad server."

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=cfg['twitchAPItoken'], client_id=cfg['twitchAPIclientID'], 
        prefix='!', initial_channels=cfg['channelSteamID_Dict'].keys())

    async def event_ready(self):
        logging.info(f'Logged in as | {self.nick} ({self.user_id})')

    @commands.command()
    async def server(self, ctx: commands.Context):
        logging.info(f"Handling !server from {ctx.author.name} in channel {ctx.channel.name}")
        serverInfo = await lookupSquadServer(cfg['channelSteamID_Dict'][ctx.channel.name], ctx.channel.name)
        await ctx.send(f'@{ctx.author.name}, {serverInfo}' )

    async def event_command_error(self, context, error):
        pass

bot = Bot()

if __name__ == "__main__":
    bot.run()
