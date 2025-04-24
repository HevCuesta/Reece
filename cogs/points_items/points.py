import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io


class PointsItemsCog(commands.Cog):
        def __init__(self, bot, conn, cursor):
            self.bot = bot
            self.conn = conn
            self.c = cursor
            print("Points and Items cog loaded")

        @commands.command()
        async def points(self, ctx, member: discord.Member = None):
            """Displays a user's points and items"""
            user_id = member.id if member else ctx.author.id
            self.c.execute("SELECT points FROM points WHERE user_id = ?", (user_id,))
            result = self.c.fetchone()
            points = result[0] if result else 0.0

            self.c.execute("SELECT item, quantity FROM inventory WHERE user_id = ?", (user_id,))
            items = self.c.fetchall()
            items_text = ", ".join([f"{item} x{quantity}" for item, quantity in items]) if items else "No items"
            
            await ctx.send(f"{member.mention if member else ctx.author.mention} has {points} points and items: {items_text}.")

        @points.error
        async def points_error(self, ctx, error):
            if isinstance(error, commands.MemberNotFound):
                await ctx.send("Member not found. Please mention a valid user.")

        @commands.command()
        async def addpoints(self, ctx, member: discord.Member, amount: float):
            """Adds (or removes) points from a user"""
            if amount >= 50:
                await ctx.send("Do not give more than 50 points at a time")
                return

            if amount < 0:
                await ctx.send("Do not send less than 0 points")
                return

            self.c.execute("INSERT INTO points (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?", 
                         (member.id, amount, amount))
            self.conn.commit()
            await ctx.send(f"{ctx.author.mention} gave {amount} points to {member.mention}.")

        @addpoints.error
        async def addpoints_error(self, ctx, error):
            if isinstance(error, commands.MemberNotFound):
                await ctx.send("Member not found. Please mention a valid user.")

        @commands.command()
        async def removepoints(self, ctx, member: discord.Member, amount: float):
            """Removes (or adds) points from a user"""
            if amount >= 50:
                await ctx.send("Do not give more than 50 points at a time")
                return

            if amount < 0:
                await ctx.send("Can't remove negative points")
                return
                
            self.c.execute("INSERT INTO points (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points - ?", 
                         (member.id, 0.0, amount))
            self.conn.commit()
            await ctx.send(f"{ctx.author.mention} removed {amount} points from {member.mention}.")

        @removepoints.error
        async def removepoints_error(self, ctx, error):
            if isinstance(error, commands.MemberNotFound):
                await ctx.send("Member not found. Please mention a valid user.")

        @commands.command()
        async def giveitem(self, ctx, member: discord.Member, quantity: int, *, item: str):
            """Gives an item to a user - !giveitem @user <quantity> <item name>"""
            self.c.execute("INSERT INTO inventory (user_id, item, quantity) VALUES (?, ?, ?) ON CONFLICT(user_id, item) DO UPDATE SET quantity = quantity + ?", 
                         (member.id, item, quantity, quantity))
            self.conn.commit()
            await ctx.send(f"{ctx.author.mention} gave {member.mention} {quantity} {item}.")

        @commands.command()
        async def removeitem(self, ctx, member: discord.Member, quantity: int, *, item: str):
            """Removes an item from a user - !removeitem @user <quantity> <item name>"""
            self.c.execute("UPDATE inventory SET quantity = MAX(0, quantity - ?) WHERE user_id = ? AND item = ?", 
                         (quantity, member.id, item))
            self.c.execute("DELETE FROM inventory WHERE user_id = ? AND item = ? AND quantity = 0", 
                         (member.id, item))
            self.conn.commit()
            await ctx.send(f"{ctx.author.mention} removed {quantity} {item} from {member.mention}.")

        @giveitem.error
        async def giveitem_error(self, ctx, error):
            if isinstance(error, commands.MemberNotFound):
                await ctx.send("Member not found. Please mention a valid user.")

        @commands.command()
        async def ranking(self, ctx):
            """Displays the top 10 users with the most points and sends a styled table"""
            self.c.execute("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10")
            ranking = self.c.fetchall()
            if not ranking:
                await ctx.send("No points data available.")
                return
            
            # Prepare data for the table
            table_data = []
            for user_id, points in ranking:
                try:
                    member = await ctx.guild.fetch_member(user_id)
                    if not member:
                        raise Exception("Member not found")
                except Exception:
                    member = None
                    member_name = "Unknown Member"
                else:
                    member_name = member.display_name
                
                # Get the user's items
                self.c.execute("SELECT item, quantity FROM inventory WHERE user_id = ?", (user_id,))
                items = self.c.fetchall()
                items_text = ", ".join([f"{item} x{quantity}" for item, quantity in items]) if items else "No items"
                table_data.append([member_name, points, items_text])

            # Create the figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))

            # Hide axes
            ax.axis("off")

            # Create the table with headers
            table = ax.table(cellText=table_data, colLabels=["User", "Points", "Items"], loc="center", cellLoc='center')

            # Styling the table
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 1.2)  # Scale the table for better readability

            # Set the header style
            for (i, j), cell in table.get_celld().items():
                if i == 0:
                    cell.set_fontsize(14)
                    cell.set_text_props(weight='bold')
                    cell.set_facecolor('#4CAF50')  # Header background color
                    cell.set_edgecolor('black')
                else:
                    cell.set_edgecolor('gray')  # Set the border color of each cell
                    cell.set_facecolor('#f2f2f2')  # Cell background color

            # Set alternating row colors
            for i, row in enumerate(table.get_celld().values()):
                if i % 2 == 1:  # Change background color for alternating rows
                    row.set_facecolor('#e6e6e6')

            # Add a title to the table
            plt.title("Top 10 Users by Points", fontsize=16, fontweight='bold')

            # Save the table to a buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)
            plt.close()

            # Send the styled table as an image
            file = discord.File(buffer, filename="ranking.png")
            await ctx.send("Here is the leaderboard table:", file=file)