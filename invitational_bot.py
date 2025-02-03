import discord
from discord.ext import commands
import random
import sqlite3
import os

# Database setup
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS helldivers (
    player_id TEXT PRIMARY KEY,
    service_number TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS illuminate (
    player_id TEXT PRIMARY KEY,
    service_number TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT
)
""")
conn.commit()
conn.close()

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    print("Democracy Officer is on duty")


@bot.command(name="enlist")
async def enlist(ctx, first_name: str = None, last_name: str = None):
    """Assigns the 'Helldiver' role, generates a 6-digit braincode, and optionally changes the player's nickname."""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")

    if ctx.channel.name == "enlistment-centre":
        guild = ctx.guild
        member = ctx.author
        human_role = discord.utils.get(guild.roles, name="Helldiver")
        zombie_role = discord.utils.get(guild.roles, name="Illuminate")

        if not human_role:
            await ctx.send("'Helldiver' role does not exist. Please create it and try again.")
            return

        if human_role in member.roles or zombie_role in member.roles:
            await ctx.send("You have already joined the game.")
            return

        await member.add_roles(human_role)

        # Generate a random 6-digit braincode
        service_number = str(random.randint(100000, 999999))

        # Default values if first_name or last_name is missing
        first_name = first_name if first_name else "Recruit"
        last_name = last_name if last_name else "Unknown"

        # Insert player info into the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO helldivers (player_id, service_number, first_name, last_name) 
            VALUES (?, ?, ?, ?)
        """, (str(member.id), service_number, first_name, last_name))
        conn.commit()
        conn.close()

        # Update player's nickname if both first and last name are provided
        if first_name and last_name:
            try:
                await member.edit(nick=f"{first_name} {last_name}")
            except discord.Forbidden:
                pass

        try:
            await member.send(f"Welcome to Operation Blinding Dawn Helldiver! Your Service Number is: {service_number}")
        except discord.Forbidden:
            await ctx.send("Failed to send DM. Please check your privacy settings.")
    else:
        await ctx.send("You must report to the enlistment centre to go on this operation!")

@bot.command(name="check_service_number")
async def check_service_number(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")
    
    # Database setup (ensure the connection is open)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get the user_id of the author who ran the command
    player_id = str(ctx.author.id)  # Convert user ID to string since it's stored as TEXT

    # Query the database to retrieve the braincode for the player_id
    cursor.execute("SELECT service_number FROM helldivers WHERE player_id = ?", (player_id,))
    result = cursor.fetchone()
    conn.close()

    # Check if a service number exists for the user
    if not result:
        await ctx.send(f"{ctx.author.mention}, you do not have an associated braincode.")
    else:
        number= result[0]  # Extract the service number from the result
        await ctx.author.send(f"Your Service Number is: `{number}`")

@bot.command(name="convert")
async def convert(ctx, service_number: str):
    """Converts a Helldiver into an Illuminate based on their service number."""
    try:
        await ctx.message.delete()  # Deletes the message that triggered the command
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")

    if ctx.channel.name != "illuminate-hive":
        await ctx.send("This command must be used in #illuminate-hive")
        return

    # Connect to the database
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Query the helldivers table for the player's details
        cursor.execute("SELECT player_id, first_name, last_name FROM helldivers WHERE service_number = ?", (service_number,))
        result = cursor.fetchone()

    except sqlite3.Error as e:
        await ctx.send(f"Database error: {e}")
        conn.close()
        return

    if not result:
        await ctx.send(f"No player found with that service number.")
        conn.close()
        return

    # Extract player details
    player_id, first_name, last_name = result

    # Retrieve the member object from the player_id
    guild = ctx.guild
    member = guild.get_member(int(player_id))
    tagger = ctx.author  # The person who used the command

    if not member:
        await ctx.send(f"Could not find a player with ID {player_id} in this server.")
        conn.close()
        return

    # Get the "Helldiver" and "Illuminate" roles
    helldiver_role = discord.utils.get(guild.roles, name="Helldiver")
    illuminate_role = discord.utils.get(guild.roles, name="Illuminate")

    if not helldiver_role or not illuminate_role:
        await ctx.send("No 'Helldiver' or 'Illuminate' roles found. Please create these roles first.")
        conn.close()
        return

    # Remove the player from 'helldivers' and add them to 'illuminate'
    try:
        # Remove player from helldivers
        cursor.execute("DELETE FROM helldivers WHERE service_number = ?", (service_number,))
        
        # Insert player into illuminate table
        cursor.execute("""
            INSERT OR REPLACE INTO illuminate (player_id, service_number, first_name, last_name) 
            VALUES (?, ?, ?, ?)
        """, (player_id, service_number, first_name, last_name))

        conn.commit()
    except sqlite3.Error as e:
        await ctx.send(f"Database error: {e}")
        conn.close()
        return
    finally:
        conn.close()

    # Role Management: Remove "Helldiver" and Add "Illuminate"
    try:
        if helldiver_role in member.roles:
            await member.remove_roles(helldiver_role)
            await member.add_roles(illuminate_role)

            # Send an announcement in the relevant channel
            tag_message = "WAAAAAAAAAGH!"
            await ctx.send(f"{member.mention} was converted by {tagger.mention}!")
            human_chat_channel = discord.utils.get(guild.text_channels, name="helldiver-garrison")
            await human_chat_channel.send(f"{member.mention} has been converted!")
        else:
            await ctx.send(f"{member.mention} is already an Illuminate.")
    except Exception as e:
        await ctx.send(f"An error occurred while converting: {e}")



@bot.command(name="check_divers")
async def check_divers(ctx):
    if ctx.channel.name != "bot-commands":
        await ctx.send("This command can only be used in the bot-commands channel.")
        return

    """Check the contents of the humans table in the database."""
    db_path = "database.db"  # Path to your database

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all rows from the Helldivers table
        cursor.execute("SELECT * FROM helldivers")
        rows = cursor.fetchall()

        # Prepare the response message
        if rows:
            response = "Contents of the Helldivers table:\n"
            for row in rows:
                response += f"{row}\n"
        else:
            response = "The Helldivers table is empty."

        # Close the connection
        conn.close()

        # Send the response
        await ctx.send(response)

    except sqlite3.OperationalError as e:
        await ctx.send(f"Database error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command(name="check_squids")
async def check_squids(ctx):
    if ctx.channel.name != "bot-commands":
        await ctx.send("This command can only be used in the bot-commands channel.")
        return

    """Check the contents of the humans table in the database."""
    db_path = "database.db"  # Path to your database

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all rows from the Helldivers table
        cursor.execute("SELECT * FROM illuminate")
        rows = cursor.fetchall()

        # Prepare the response message
        if rows:
            response = "Contents of the Illuminate table:\n"
            for row in rows:
                response += f"{row}\n"
        else:
            response = "The Illuminate table is empty."

        # Close the connection
        conn.close()

        # Send the response
        await ctx.send(response)

    except sqlite3.OperationalError as e:
        await ctx.send(f"Database error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")
        
@bot.command(name="revive")
async def revive(ctx, service_number: str):
    """Revives a player based on their service number and returns them to the Helldivers."""
    try:
        await ctx.message.delete()  # Deletes the message that triggered the command
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")

    if ctx.channel.name != "bot-commands":
        await ctx.send("This command must be used in the #bot-commands channel.")
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Check if the service number exists in the 'illuminate' table ()
    cursor.execute("SELECT player_id, first_name, last_name FROM illuminate WHERE service_number = ?", (service_number,))
    result = cursor.fetchone()

    if not result:
        await ctx.send("No player found with that service number, or the player is not dead.")
        conn.close()
        return

    # Extract player information
    player_id, first_name, last_name = result

    # Retrieve the member object from the player_id
    guild = ctx.guild
    member = guild.get_member(int(player_id))
    
    if not member:
        await ctx.send(f"Could not find the player with ID {player_id} in this server.")
        conn.close()
        return

    # Get the "Helldiver" (human) and "Illuminate" (zombie) roles
    helldiver_role = discord.utils.get(guild.roles, name="Helldiver")
    illuminate_role = discord.utils.get(guild.roles, name="Illuminate")

    # Check if roles exist
    if not helldiver_role or not illuminate_role:
        await ctx.send("Please make sure 'Helldiver' and 'Illuminate' roles exist on the server.")
        conn.close()
        return

    # Remove "Illuminate" role and add "Helldiver" role
    try:
        if illuminate_role in member.roles:
            await member.remove_roles(illuminate_role)
            await member.add_roles(helldiver_role)

            # Generate a new 6-digit service number for the revived player
            new_service_number = str(random.randint(100000, 999999))

            # Remove the player from the 'illuminate' table and add them back to 'helldivers'
            cursor.execute("DELETE FROM illuminate WHERE service_number = ?", (service_number,))
            cursor.execute("""
                INSERT OR REPLACE INTO helldivers (player_id, service_number, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            """, (member.id, new_service_number, first_name, last_name))
            conn.commit()

            # Notify in relevant channels and DM the player
            human_chat_channel = discord.utils.get(guild.text_channels, name="helldiver-garrison")
            zombie_chat_channel = discord.utils.get(guild.text_channels, name="illuminate-hive")
            
            if human_chat_channel:
                await human_chat_channel.send(f"{member.mention} has been revived and is now a Helldiver again!")
            if zombie_chat_channel:
                await zombie_chat_channel.send(f"{member.mention} has been revived and is no longer an Illuminate!")

            await ctx.send(f"Player has been revived successfully")

            try:
                await member.send(f"You have been revived! Your new service number is: {new_service_number}")
            except discord.Forbidden:
                return
        else:
            await ctx.send(f"{member.mention} is not an Illuminate.")
    except Exception as e:
        await ctx.send(f"An error occurred while reviving: {e}")
    finally:
        conn.close()

@bot.command(name="reset")
async def reset(ctx):
    """Resets the game, reviving all players and assigning new service numbers."""
    
    if ctx.channel.name != "bot-commands":
        await ctx.send("This command can only be used in the #bot-commands channel.")
        return

    guild = ctx.guild
    helldiver_role = discord.utils.get(guild.roles, name="Helldiver")
    illuminate_role = discord.utils.get(guild.roles, name="Illuminate")

    if not helldiver_role or not illuminate_role:
        await ctx.send("The 'Helldiver' or 'Illuminate' roles are missing. Please create them first.")
        return

    # Remove all players from Illuminate and add them back to Helldivers
    for member in guild.members:
        try:
            if illuminate_role in member.roles:
                await member.remove_roles(illuminate_role)
                await member.add_roles(helldiver_role)
        except discord.Forbidden:
            await ctx.send(f"Could not reset roles for {member.display_name}.")

    # Connect to the database and reset tables
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM helldivers")
    cursor.execute("DELETE FROM illuminate")
    conn.commit()

    # Restore all Helldivers with a new service number
    for member in guild.members:
        if helldiver_role in member.roles:
            new_service_number = str(random.randint(100000, 999999))

            # Try to preserve their original first and last name from the database
            cursor.execute("SELECT first_name, last_name FROM helldivers WHERE player_id = ?", (str(member.id),))
            name_result = cursor.fetchone()

            first_name = name_result[0] if name_result else "Unknown"
            last_name = name_result[1] if name_result else "Soldier"

            cursor.execute("""
                INSERT INTO helldivers (player_id, service_number, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            """, (str(member.id), new_service_number, first_name, last_name))

            try:
                await member.send(f"Your new service number is: {new_service_number}")
            except discord.Forbidden:
                await ctx.send(f"Could not DM {member.display_name}.")

    conn.commit()
    conn.close()
    await ctx.send("Game has been reset. All players are now Helldivers with new service numbers.")

@bot.command(name="end")
async def end(ctx):
    # Ensure the command is run in the correct channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("You cannot stop the bot from this channel.")
        return

    guild = ctx.guild
    human_role = discord.utils.get(guild.roles, name="Helldiver")
    zombie_role = discord.utils.get(guild.roles, name="Illuminate")

    db_path = "database.db"
    if not os.path.exists(db_path):
        await ctx.send("Database file not found. Nothing to clean.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query both tables for user IDs
    cursor.execute("SELECT player_id FROM helldivers")
    user_ids_table1 = cursor.fetchall()

    cursor.execute("SELECT player_id FROM illuminate")  # Replace 'other_table' with the actual table name
    user_ids_table2 = cursor.fetchall()

    conn.close()

    # Combine and deduplicate user IDs from both tables
    user_ids = {int(user_id[0]) for user_id in user_ids_table1 + user_ids_table2}

    if not user_ids:
        await ctx.send("No users found in the database. Nothing to clean.")
        return

    # Iterate over the user IDs and remove roles
    for user_id in user_ids:
        member = guild.get_member(user_id)
        if member:
            try:
                await member.remove_roles(human_role, zombie_role)
            except discord.Forbidden:
                await ctx.send(f"Could not remove roles for {member.display_name}.")
            except Exception as e:
                await ctx.send(f"An error occurred while removing roles: {e}")

    # Delete the database file
    try:
        os.remove(db_path)
        await ctx.send("Database wiped successfully.")
    except Exception as e:
        await ctx.send(f"Failed to delete database: {e}")

    # Shut down the bot
    await ctx.send("Tagger has been shut down, roles removed, and database wiped.")
    await bot.close()


# Run the bot
TOKEN = "MTMzNTYzODgyNTg2MjQzNDkxOA.GxIIT2.nX8XS7o_7VbU8EPMlyA_3YiA6UXEj-TdVe3gPA"
bot.run(TOKEN)
