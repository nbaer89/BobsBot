import discord
import settings
import pygsheets
import pickle

from discord.ext import commands


class Ghostball(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # Loads Google Sheets
        self.gSheet = pygsheets.authorize(client_secret=settings.GSHEET_CRED)
        self.sh = self.gSheet.open_by_key(settings.CALCULATOR_KEY)
        self.hud = self.sh.worksheet_by_title(settings.CALCULATOR_SHEET)
        self.rec_sh = self.gSheet.open_by_key(settings.RECORD_KEY)
        self.playerList = self.rec_sh.worksheet_by_title(settings.PLAYERLIST_SHEET)
        self.gbData = self.rec_sh.worksheet_by_title(settings.DATA_SHEET)
        # Initialize shared instance variables
        self.swings = {}
        # Set game number to current game in record
        self.game_number = int(self.gbData.get_col(1, include_tailing_empty=False)[-1])
        # Set pitcher to last pitcher in record
        self.pitcher_name = str(self.gbData.get_col(4, include_tailing_empty=False)[-1])
        # Set pitch_id to next pitch
        self.pitch_id = int(self.gbData.get_col(2, include_tailing_empty=False)[-1]) + 1
        try:
            self.batter_list = pickle.load(open('batters.p', 'rb'))
        except FileNotFoundError:
            self.batter_list = {}

    # game command
    @commands.command()
    @commands.has_role("Crawdads")
    async def game(self, ctx, *args: str):
        """Changes the game number. Usage $game or $game <number>"""
        if len(args) == 0:
            self.game_number = int(self.gbData.get_col(1, include_tailing_empty=False)[-1]) + 1
        elif len(args) == 1:
            self.game_number = args[0]
        else:
            await ctx.send(
                f'Usage is "{settings.COMMAND_PREFIX}game" or "{settings.COMMAND_PREFIX}game number"')
            return
        await ctx.send(f'Game number set to {self.game_number}')
        await ctx.message.delete()

    # pitcher command
    @commands.command()
    @commands.has_role("Crawdads")
    async def pitcher(self, ctx, *, arg: str):
        """Changes the current pitcher. Usage: $pitcher <Pitcher Name>"""
        if any(arg in sublist for sublist in self.playerList.get_col(1, include_tailing_empty=False)):
            self.pitcher_name = arg
            await ctx.send(f'{self.pitcher_name} is the new pitcher')
        else:
            await ctx.send(f'{arg} does not exist. Check spelling')
        await ctx.message.delete()

    # pitch command
    @commands.command()
    @commands.has_role("Crawdads")
    async def pitch(self, ctx, pitch_number: int):
        """Calculates swings for entered pitch. Usage: $pitch <number>"""
        self.hud.update_value(settings.PITCHER_CELL, self.pitcher_name)  # Updates calculator with current pitcher.
        if pitch_number not in range(1, 1001, 1):
            await ctx.send(f'Pitch must be a number between 1 and 1000.')
        else:
            results = f"{self.pitcher_name}'s pitch was {pitch_number}."
            self.hud.update_value(settings.PITCH_CELL, pitch_number)  # Enters pitch number in calculator.
            for (current_batter_discord, current_swing) in self.swings.items():
                current_batter = self.batter_list.get(str(current_batter_discord))
                self.hud.update_value(settings.BATTER_CELL, current_batter)  # Add batter to calculator
                self.hud.update_value(settings.SWING_CELL, current_swing)  # Enters swing number in calculator
                # diff = self.hud.get_value(settings.DIFF_CELL) # Get diff from calculator NOT USED
                if abs(current_swing - pitch_number) > 500:  # Get diff from code for performance increase
                    diff = 1000 - abs(current_swing - pitch_number)
                else:
                    diff = abs(current_swing - pitch_number)
                result = self.hud.get_value(settings.RESULT_CELL)
                results += f"\n{current_batter_discord.display_name} swung {current_swing}. Diff = {diff}. Result = {result}."
                self.gbData.append_table(
                    [self.game_number, str(self.pitch_id), str(current_batter_discord), self.pitcher_name, current_swing,
                     pitch_number, diff, result], start='A1')
            self.swings = {}  # Clear all previous swings
            await ctx.send(results)
            self.pitch_id += 1
        await ctx.message.delete()

    # swing command
    @commands.command()
    @commands.has_role("Crawdads")
    async def swing(self, ctx, swing_number: int):
        """Enters your guess swing. Usage: $swing <number>"""
        if swing_number not in range(1, 1001, 1):
            await ctx.send(f'Swing a number between 1 and 1000.')
        elif self.batter_list.get(str(ctx.author)):
            self.swings[ctx.author] = swing_number
            await ctx.send(f'{ctx.author.mention} swings {swing_number}')
        else:
            await ctx.send(f'{ctx.author.mention} has not registered as a batter. Register with the $register command. '
                           f'Usage: $register <MLN Stats Name>. Spelling matters.')
        await ctx.message.delete()

    @commands.command()
    @commands.has_role("Crawdads")
    async def register(self, ctx, *args):
        batter_name = ' '.join(args)
        if len(args) == 0:
            await ctx.send(f'Register yourself as a batter. Usage: $register <MLN Stats Name>')
        elif any(batter_name in sublist for sublist in self.playerList.get_col(1, include_tailing_empty=False)):
            self.batter_list[str(ctx.author)] = batter_name
            await ctx.send(f'Associated {str(ctx.author)} with {batter_name}')
            pickle.dump(self.batter_list, open('batters.p', 'wb'))
        else:
            await ctx.send(f'{batter_name} is not a player.')
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Ghostball(bot))
