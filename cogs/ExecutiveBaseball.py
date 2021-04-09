import settings
import pygsheets

from fuzzywuzzy import process
from datetime import datetime
from discord.ext import commands


pots_channel = 735301496891113512


def is_channel(channel_id):
    async def predicate(ctx):
        return ctx.message.channel.id == channel_id
    return commands.check(predicate)


class ExecutiveBaseball(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # Loads Google Sheets
        self.gSheet = pygsheets.authorize(client_secret=settings.GSHEET_CRED)
        self.sheet = self.gSheet.open_by_key(settings.XBA_KEY)
        self.options_tracker = self.sheet.worksheet_by_title(settings.XBA_OPTION_SHEET)
        self.team_list = self.sheet.worksheet_by_title(settings.XBA_TEAMLIST_SHEET)
        self.team_list_records = self.team_list.get_all_records()
        self.transaction_log = self.sheet.worksheet_by_title(settings.XBA_TRANSACTION_LOG_SHEET)

    def get_team(self, discord_id):
        team = None
        for x in self.team_list_records:
            if x["OwnerID"] == discord_id:
                team = x["Team"]
        return team

    def get_player(self, player):
        for index, row in enumerate(self.options_tracker):
            if row[1] == player:
                return index + 1
        return False

    async def get_similar_player(self, ctx, player, choices):
        similar_results = process.extract(player, self.options_tracker.get_col(2, include_tailing_empty=False),
                                          limit=choices)
        await ctx.send(f"{player} not found. Did you mean: (enter 1-{choices})")
        for x, y in enumerate(similar_results):
            await ctx.send(f"{x + 1}) {y[0]}?")
        msg = await self.bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if msg.content not in [str(i) for i in range(1, choices + 1)]:
            await ctx.send(f'{player} not found. Check spelling and try again.')
        else:
            return similar_results[int(msg.content) - 1][0]
        return False

    @commands.command()
    @commands.has_role("Executive")
    @is_channel(pots_channel)
    async def option(self, ctx, *, player: str):
        team = self.get_team(ctx.author.id)
        player_found = False
        if team is None:
            await ctx.send(f'{ctx.author.mention} is not an executive.')
        else:
            while not player_found:
                row = self.get_player(player)
                if not row:
                    player = await self.get_similar_player(ctx, player, 3)
                else:
                    player_found = True
                    if self.options_tracker[row][0] == team:
                        options_used = int(self.options_tracker[row][2])
                        if 3 - options_used <= 0:
                            await ctx.send(
                                f'{player} does not have any options remaining and must be placed on waivers.'
                            )
                        else:
                            options_used += 1
                            self.transaction_log.append_table(
                                [str(datetime.utcnow()), team, 'Option to Minors', player])
                            await ctx.send(
                                f'{team} optioned {player}, {3 - options_used} options remaining. Remember to $recall '
                                f'a player from the minors. '
                            )
                    else:
                        await ctx.send(f'{team} does not own {player}')

    @commands.command(name="IL")
    @commands.has_role("Executive")
    @is_channel(pots_channel)
    async def injured_list(self, ctx, *, player: str):
        team = self.get_team(ctx.author.id)
        player_found = False
        if team is None:
            await ctx.send(f'{ctx.author.mention} is not an executive.')
        else:
            while not player_found:
                row = self.get_player(player)
                if not row:
                    player = await self.get_similar_player(ctx, player, 3)
                else:
                    player_found = True
                    if self.options_tracker[row][0] == team:
                        self.transaction_log.append_table([str(datetime.utcnow()), team, 'Injured List', player])
                        await ctx.send(
                            f'{team} placed {player} on the injured list. Remember to $recall a player from the minors.'
                        )
                    else:
                        await ctx.send(f'{team} does not own {player}')

    @commands.command()
    @commands.has_role("Executive")
    @is_channel(pots_channel)
    async def recall(self, ctx, *, player: str):
        team = self.get_team(ctx.author.id)
        player_found = False
        if team is None:
            await ctx.send(f'{ctx.author.mention} is not an executive.')
        else:
            while not player_found:
                row = self.get_player(player)
                if not row:
                    player = await self.get_similar_player(ctx, player, 3)
                else:
                    player_found = True
                    if self.options_tracker[row][0] == team or self.option[row][0] == "NONE":
                        self.transaction_log.append_table(
                            [str(datetime.utcnow()), team, 'Recalled (Add to Majors)', player])
                        await ctx.send(
                            f'{team} recalled {player} from the minors.'
                        )
                    else:
                        await ctx.send(f'{team} does not own {player}')

    @commands.command(name='16man')
    @commands.has_role("Executive")
    @is_channel(pots_channel)
    async def sixteen_man(self, ctx, *, player: str):
        team = self.get_team(ctx.author.id)
        player_found = False
        if team is None:
            await ctx.send(f'{ctx.author.mention} is not an executive.')
        else:
            while not player_found:
                row = self.get_player(player)
                if not row:
                    player = await self.get_similar_player(ctx, player, 3)
                else:
                    player_found = True
                    if self.options_tracker[row][0] == team:
                        self.transaction_log.append_table([str(datetime.utcnow()), team, '16th Man Designated', player])
                        await ctx.send(
                            f'{team} placed {player} as 16th man designation.'
                        )
                    else:
                        await ctx.send(f'{team} does not own {player}')

    @commands.command()
    @commands.has_role("Executive")
    @is_channel(pots_channel)
    async def player(self, ctx, *, player: str):
        player_found = False
        while not player_found:
            row = self.get_player(player)
            if not row:
                player = await self.get_similar_player(ctx, player, 3)
            else:
                team = self.options_tracker[row][0]
                options_used = int(self.options_tracker[row][2])
                await ctx.send(f"{player} is owned by {team} and has {3 - options_used} options remaining.")
                player_found = True

    @commands.command()
    @commands.has_role("Executive")
    @is_channel(pots_channel)
    async def drive(self, ctx):
        await ctx.author.send("https://docs.google.com/spreadsheets/d/1fPO3Z-XZqj5aNhapwAfBhLt7L40JX6AJJscTjWernaE"
                              "/edit?usp=drive_web&ouid=112131933844324382255")
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(ExecutiveBaseball(bot))
