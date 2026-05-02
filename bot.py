import discord
from discord.ext import commands
import asyncio
import os

# ========================
# КОНФИГУРАЦИЯ
# ========================
TOKEN = os.environ.get('TOKEN')
MEMBER_ROLE_ID = 1497214361490423858   # Роля - на тези се прави канал
ADMIN_ROLE_ID  = 1333904909858242580   # Роля - тези могат да пишат !done
CATEGORY_NAME  = 'Кръвен-Договор'
# ========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'✅ Ботът е онлайн като: {bot.user}')


@bot.event
async def on_member_update(before, after):
    new_roles = set(after.roles) - set(before.roles)
    member_role = discord.utils.get(after.guild.roles, id=MEMBER_ROLE_ID)

    if member_role not in new_roles:
        return

    guild = after.guild
    member = after

    # 1. Намери или създай категорията
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

    if category is None:
        overwrites_category = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
        }
        category = await guild.create_category(name=CATEGORY_NAME, overwrites=overwrites_category)
        print(f'📁 Създадена категория: {CATEGORY_NAME}')

    # 2. Название на канала
    channel_name = (
        member.name.lower().replace(' ', '-')[:90]
    ) or f'потребител-{member.id}'

    # 3. Провери дали вече съществува
    existing = discord.utils.get(category.channels, name=channel_name)
    if existing:
        print(f'⚠️ Каналът #{channel_name} вече съществува.')
        return

    # 4. Права — членът вижда канала, admin ролята също, @everyone не
    admin_role = discord.utils.get(guild.roles, id=ADMIN_ROLE_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        ),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }

    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )

    new_channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites,
    )

    await new_channel.send(
        f'🩸 Добре дошъл, {member.mention}! Това е твоят личен канал в **{CATEGORY_NAME}**.'
    )

    print(f'✅ Създаден канал: #{channel_name} за: {member.name}')


@bot.command(name='done')
async def done(ctx):
    # Само в категория "Кръвен-Договор"
    if ctx.channel.category is None or ctx.channel.category.name != CATEGORY_NAME:
        return

    # Само тези с ADMIN_ROLE_ID могат да изпълнят !done
    admin_role = discord.utils.get(ctx.guild.roles, id=ADMIN_ROLE_ID)
    if admin_role not in ctx.author.roles:
        await ctx.send('❌ Нямаш право да затвориш този канал.')
        return

    await ctx.send('✅ Каналът ще бъде изтрит след 5 секунди...')
    await asyncio.sleep(5)
    await ctx.channel.delete(reason=f'!done от {ctx.author.name}')
    print(f'🗑️ Изтрит канал: #{ctx.channel.name} от: {ctx.author.name}')


bot.run(TOKEN)
