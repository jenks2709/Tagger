import discord
from discord.ext import commands
import random
import sqlite3
import os

# Load the list of words from words.txt
with open("words.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

# Database setup
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS humans (
    player_id TEXT PRIMARY KEY,
    braincode TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS zombies (
    player_id TEXT PRIMARY KEY,
    braincode TEXT NOT NULL,
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
    print("Tagger is online and ready to run")


@bot.command()
async def join(ctx, first_name: str = None, last_name: str = None):
    """Assigns the 'Human' role, generates a braincode, and optionally changes the player's nickname."""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")
    if ctx.channel.name == "join":
        guild = ctx.guild
        member = ctx.author
        human_role = discord.utils.get(guild.roles, name="Human")
        zombie_role = discord.utils.get(guild.roles, name="Zombie")

        if not human_role:
            await ctx.send("'Human' role does not exist. Please create it and try again.")
            return

        if human_role in member.roles or zombie_role in member.roles:
            await ctx.send("You have already joined the game.")
            return

        await member.add_roles(human_role)

        braincode = "".join(random.sample(words, 3))
        # Insert player info into the database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()   
        cursor.execute("""
            INSERT OR REPLACE INTO humans (player_id, braincode, first_name, last_name) 
            VALUES (?, ?, ?, ?)
        """, (str(member.id), braincode, first_name, last_name))
        conn.commit()
        conn.close()
        if first_name and last_name:
            try:
                await member.edit(nick=f"{first_name} {last_name}")
            except discord.Forbidden:
                pass

        try:
            await member.send(f"Your braincode is: **`{braincode}`**\n*Keep it secret, Keep it safe!*")
        except discord.Forbidden:
            await ctx.send("Failed to send DM. Please check your privacy settings.")
    else:
        await ctx.send("You must use this command in the #join channel")

@bot.command(name="check_braincode")
async def check_braincode(ctx):
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
    cursor.execute("SELECT braincode FROM humans WHERE player_id = ?", (player_id,))
    result = cursor.fetchone()
    conn.close()

    # Check if a braincode exists for the user
    if not result:
        await ctx.send(f"{ctx.author.mention}, you do not have an associated braincode.")
    else:
        braincode = result[0]  # Extract the braincode from the result
        await ctx.author.send(f"{ctx.author.mention}, your braincode is: `{braincode}`")


@bot.command(name="tag")
async def tag(ctx, braincode: str):
    """
    Handles the tagging process, converting a Human into a Zombie,
    and includes a random message from a .txt file in the announcement.
    """
    
    
    try:
        await ctx.message.delete()  # Deletes the message that triggered the command
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")
    if ctx.channel.name != "zombie-chat":
        await ctx.send("This command must be used in #zombie-chat")
        return

    # Connect to the human database
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Query the human database for the player_id associated with the braincode
        cursor.execute("SELECT player_id, braincode, first_name, last_name FROM humans WHERE braincode = ?", (braincode,))
        result = cursor.fetchone()
        

    except sqlite3.Error as e:
        await ctx.send(f"Database error: {e}")
        return

    if not result:
        await ctx.send(f"No player found with that braincode.")
        return

    # Extract the player_id from the database result
    player_id = result[0]
    first_name = result[2]
    last_name = result[3]

    # Retrieve the member object from the player_id
    guild = ctx.guild
    member = guild.get_member(int(player_id))  # Convert player_id to an integer if stored as TEXT
    tagger = ctx.author
    human_chat_channel = discord.utils.get(guild.text_channels, name="human-chat")
    zombie_chat_channel = discord.utils.get(guild.text_channels, name="zombie-chat")

    cursor.execute("INSERT OR REPLACE INTO zombies (player_id, braincode, first_name, last_name) VALUES (?, ?, ?, ?)", (member.id, braincode, first_name, last_name))
    cursor.execute("DELETE FROM humans WHERE braincode = ?", (braincode,))
    conn.commit()
    conn.close()

    if not member:
        await ctx.send(f"Could not find a player with ID {player_id} in this server.")
        return

    # Get the "Human" and "Zombie" roles
    human_role = discord.utils.get(guild.roles, name="Human")
    zombie_role = discord.utils.get(guild.roles, name="Zombie")

    # Check if the roles exist
    if not human_role or not zombie_role:
        await ctx.send("No 'Human' or 'Zombie' roles found. Please create these roles first.")
        return

    # Remove "Human" role and add "Zombie" role if applicable
    try:
        if human_role in member.roles:
            await member.remove_roles(human_role)
            await member.add_roles(zombie_role)

            # Load a random message from the .txt file
            try:
                with open("death_messages.txt", "r") as f:
                    messages = [line.strip() for line in f if line.strip()]  # Exclude empty lines
                tag_message = random.choice(messages) if messages else "The infection spreads further..."
            except FileNotFoundError:
                tag_message = "The infection spreads further..."  # Default message if file not found
            if human_chat_channel:
                if member.id == 560509176669798440:
                    gif_path = "badspeed_deployed.gif"
                    await human_chat_channel.send(f"{member.mention} was tagged!", file=discord.File(gif_path))
                else:
                    await ctx.send(f"{member.mention} was tagged by {tagger.mention}! {tag_message}")
            if zombie_chat_channel:
                await ctx.send(f"{member.mention} was tagged by {tagger.mention}!")
        else:
            await ctx.send(f"{member.mention} is already a Zombie.")
    except Exception as e:
        await ctx.send(f"An error occurred while tagging: {e}")


@bot.command(name="check_humans")
async def check_humans(ctx):
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
        cursor.execute("SELECT * FROM humans")
        rows = cursor.fetchall()

        # Prepare the response message
        if rows:
            response = "Human Players:\n"
            for row in rows:
                response += f"{row}\n"
        else:
            response = "There are no Humans."

        # Close the connection
        conn.close()

        # Send the response
        await ctx.send(response)

    except sqlite3.OperationalError as e:
        await ctx.send(f"Database error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command(name="check_zombies")
async def check_zombies(ctx):
    if ctx.channel.name != "bot-commands":
        await ctx.send("This command can only be used in the bot-commands channel.")
        return

    """Check the contents of the humans table in the database."""
    db_path = "database.db"  # Path to your database

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all rows from the Zombies table
        cursor.execute("SELECT * FROM zombies")
        rows = cursor.fetchall()

        # Prepare the response message
        if rows:
            response = "Zombie Players:\n"
            for row in rows:
                response += f"{row}\n"
        else:
            response = "There are no Zombies."

        # Close the connection
        conn.close()

        # Send the response
        await ctx.send(response)

    except sqlite3.OperationalError as e:
        await ctx.send(f"Database error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")
        
@bot.command(name="revive")
async def revive(ctx, braincode: str):
    """Revives a player based on their braincode and returns them to the Humans."""
    try:
        await ctx.message.delete()  # Deletes the message that triggered the command
    except discord.Forbidden:
        await ctx.send("I do not have permission to delete messages.")

    if ctx.channel.name != "bot-commands":
        await ctx.send("This command must be used in the #bot-commands channel.")
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Check if the braincode exists in the 'zombie' table ()
    cursor.execute("SELECT player_id, first_name, last_name FROM zombies WHERE braincode = ?", (braincode,))
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

    # Get the "Human" and "Zombie" roles
    human_role = discord.utils.get(guild.roles, name="Human")
    zombie_role = discord.utils.get(guild.roles, name="Zombie")

    # Check if roles exist
    if not human_role or not zombie_role:
        await ctx.send("Please make sure 'Human' and 'Zombie' roles exist on the server.")
        conn.close()
        return

    # Remove "Zombie" role and add "Human" role
    try:
        if zombie_role in member.roles:
            await member.remove_roles(zombie_role)
            await member.add_roles(human_role)

            # Generate a new 6-digit service number for the revived player
            new_braincode = "".join(random.sample(words, 3))

            # Remove the player from the 'Zombie' table and add them back to 'Humans'
            cursor.execute("DELETE FROM zombies WHERE braincode = ?", (braincode,))
            cursor.execute("""
                INSERT OR REPLACE INTO humans (player_id, braincode, first_name, last_name) 
                VALUES (?, ?, ?, ?)
            """, (member.id, new_braincode, first_name, last_name))
            conn.commit()

            # Notify in relevant channels and DM the player
            human_chat_channel = discord.utils.get(guild.text_channels, name="human-chat")
            zombie_chat_channel = discord.utils.get(guild.text_channels, name="zombie chat")
            
            if human_chat_channel:
                await human_chat_channel.send(f"{member.mention} has been revived and is now a Human again!")
            if zombie_chat_channel:
                await zombie_chat_channel.send(f"{member.mention} has been revived and is no longer a Zombie!")

            await ctx.send(f"Player has been revived successfully")

            try:
                await member.send(f"You have been revived! Your new braincode is: {new_braincode}")
            except discord.Forbidden:
                return
        else:
            await ctx.send(f"{member.mention} is not an Zombie.")
    except Exception as e:
        await ctx.send(f"An error occurred while reviving: {e}")
    finally:
        conn.close()

@bot.command(name="reset")
async def reset(ctx):
    if ctx.channel.name != "bot-commands":
        await ctx.send("This command can only be used in the bot-commands channel.")
        return

    guild = ctx.guild
    human_role = discord.utils.get(guild.roles, name="Human")
    zombie_role = discord.utils.get(guild.roles, name="Zombie")

    for member in guild.members:
        try:
            if zombie_role in member.roles:
                await member.remove_roles(zombie_role)
                await member.add_roles(human_role)
        except discord.Forbidden:
            await ctx.send(f"Could not reset roles for {member.display_name}.")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM humans")
    cursor.execute("DELETE FROM zombies")
    conn.commit()

    for member in guild.members:
        if human_role in member.roles:
            braincode = "".join(random.sample(words, 3))
            cursor.execute("INSERT INTO humans (player_id, braincode) VALUES (?, ?)", (str(member.id), braincode))
            try:
                await member.send(f"Your new braincode is: **`{braincode}`**\n*Keep it secret, keep it safe!*")
            except discord.Forbidden:
                await ctx.send(f"Could not DM {member.display_name}.")
    conn.commit()
    conn.close()
    await ctx.send("Game has been reset.")

@bot.command(name="end")
async def end(ctx):
    # Ensure the command is run in the correct channel
    if ctx.channel.name != "bot-commands":
        await ctx.send("You cannot stop the bot from this channel.")
        return

    guild = ctx.guild
    human_role = discord.utils.get(guild.roles, name="Human")
    zombie_role = discord.utils.get(guild.roles, name="Zombie")

    db_path = "database.db"
    if not os.path.exists(db_path):
        await ctx.send("Database file not found. Nothing to clean.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query both tables for user IDs
    cursor.execute("SELECT player_id FROM humans")
    user_ids_table1 = cursor.fetchall()

    cursor.execute("SELECT player_id FROM zombies") 
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
with open("token.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read()
bot.run(TOKEN)
