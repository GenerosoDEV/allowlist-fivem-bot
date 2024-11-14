import dotenv, discord, os, asyncio, json, datetime, requests
from discord.ext import commands, tasks
from discord import app_commands

client = commands.Bot("g!", intents=discord.Intents.all())
client.remove_command("help")

dotenv.load_dotenv()

with open("./config.json", "r", encoding='utf-8') as f:
    CONFIG = json.load(f)

APPROVED_ROLE = CONFIG['APPROVED_ROLE']
APPROVED_CHANNEL = CONFIG['APPROVED_CHANNEL']
FAILED_CHANNEL = CONFIG['FAILED_CHANNEL']
ROLE_TO_REMOVE = CONFIG['ROLE_TO_REMOVE']
REASONS = CONFIG['REASONS']
FIVEM_IP = CONFIG['FIVEM_IP']
FIVEM_PORT = CONFIG['FIVEM_PORT']
STATUS_CHANNEL = CONFIG['STATUS_CHANNEL']
PLAYERS_CHANNEL = CONFIG['PLAYERS_CHANNEL']
STATUS_ONLINE_TEXT = CONFIG['STATUS_ONLINE_TEXT']
STATUS_OFFLINE_TEXT = CONFIG['STATUS_OFFLINE_TEXT']
PLAYERS_TEXT = CONFIG['PLAYERS_TEXT']

@tasks.loop(minutes=5)
async def atualizar_server_info():
    try:
        url = f"http://{FIVEM_IP}:{FIVEM_PORT}/players.json"  # URL da API para obter informações sobre os jogadores
        qtd_players = 0
        status = False
        try:
            resposta = requests.get(url)
            resposta.raise_for_status()  # Garante que a requisição foi bem-sucedida
            players = resposta.json()  # Converte a resposta para um objeto JSON
            
            # Retorna a quantidade de jogadores online
            qtd_players = len(players)
            status = True
        except requests.exceptions.RequestException as e:
            qtd_players = 0
            status = False
        finally:
            c_status = client.get_channel(STATUS_CHANNEL)
            c_players = client.get_channel(PLAYERS_CHANNEL)
            if status:
                await c_status.edit(name=STATUS_ONLINE_TEXT)
            else:
                await c_status.edit(name=STATUS_OFFLINE_TEXT)

            text = PLAYERS_TEXT.replace("<players>", str(qtd_players))
            await c_players.edit(name=text)
    except Exception as e:
        print(f"Erro na atualização de info do server: {e}")

    
@client.event
async def on_ready():
    try:
        try:
            await atualizar_server_info.start()
        except: 
            pass
        print(f"\n\nID: {client.user.id}\nNome: {client.user}")
        await app_commands.CommandTree.sync(client.tree)
        print("Slash commands sincronizados!")
        await client.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Gringa RP - Allowlist!"))
    except Exception as e:
        print(f"Erro nas logs de inicialização: {e}")

@client.tree.command()
async def aprovar(inter: discord.Interaction, membro: discord.Member):
    await inter.response.defer(ephemeral=True)
    try:
        if membro and membro in inter.guild.members:
            embed = discord.Embed(title="Novo Usuário Aprovado", color=0x00ff00, description=f"O usuário {membro.mention} foi **aprovado** na allowlist.\n\nBem-vindo à **Liberty City!** Esperamos que aproveite sua experiência aqui.")
            embed.set_thumbnail(url="https://media.discordapp.net/attachments/1012098789840015551/1273016215329181716/GRINGALOGOBOT.png")
            embed.set_image(url="https://media.discordapp.net/attachments/1012098789840015551/1273016980235878511/gringa.png")
            embed.set_footer(text="Gringa Liberty City © Todos os direitos reservados", icon_url="https://media.discordapp.net/attachments/1012098789840015551/1273016215329181716/GRINGALOGOBOT.png")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            
            await membro.add_roles(inter.guild.get_role(APPROVED_ROLE))
            await membro.remove_roles(inter.guild.get_role(ROLE_TO_REMOVE))

            await client.get_channel(APPROVED_CHANNEL).send(embed=embed)
            await inter.followup.send(f"{membro.mention} aprovado com sucesso!", ephemeral=True)
            return
        
        await inter.followup.send(f"Esse membro não existe ou não está no servidor.", ephemeral=True)
    except Exception as e:
        print("Erro inesperado: " + str(e))
        await inter.followup.send("Erro inesperado: " + str(e))

@client.tree.command()
async def reprovar(inter: discord.Interaction, membro: discord.Member, motivo1: str, motivo2: str=None, observacoes: str = None):
    await inter.response.defer(ephemeral=True)
    try:
        if motivo1 not in REASONS or motivo2 not in REASONS:
            await inter.followup.send("Você deve escolher motivos válidos da lista.", ephemeral=True)
            return
        if membro and membro in inter.guild.members:
            embed = discord.Embed(title="Usuário Reprovado", color=0xff0000, description=f"`O usuário {membro.mention} foi **reprovado** na allowlist.\nNão desanime, você ainda pode tentar novamente!")
            embed.add_field(name="Motivo 1", value=motivo1)
            if motivo2:
                embed.add_field(name="Motivo 2", value=motivo2)
            if observacoes:
                embed.add_field(name="Observações", value=observacoes)
            embed.set_thumbnail(url="https://media.discordapp.net/attachments/1012098789840015551/1273016215329181716/GRINGALOGOBOT.png")
            embed.set_image(url="https://media.discordapp.net/attachments/1012098789840015551/1273016980235878511/gringa.png")
            embed.set_footer(text="Gringa Liberty City © Todos os direitos reservados", icon_url="https://media.discordapp.net/attachments/1012098789840015551/1273016215329181716/GRINGALOGOBOT.png")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

            await client.get_channel(FAILED_CHANNEL).send(embed=embed)
            await inter.followup.send(f"{membro.mention} reprovado com sucesso!", ephemeral=True)
            return
        await inter.followup.send(f"Esse membro não existe ou não está no servidor.", ephemeral=True)
    except Exception as e:
        print("Erro inesperado: " + str(e))
        await inter.followup.send("Erro inesperado: " + str(e))

@reprovar.autocomplete("motivo1")
async def motivo1_autocomplete(inter: discord.Interaction, current: str):
    return [app_commands.Choice(name=motivo, value=motivo) for motivo in REASONS if current.lower() in motivo.lower()]

@reprovar.autocomplete("motivo2")
async def motivo2_autocomplete(inter: discord.Interaction, current: str):
    return [app_commands.Choice(name=motivo, value=motivo) for motivo in REASONS if current.lower() in motivo.lower()]

@client.event
async def on_application_command_error(inter: discord.Interaction, error: Exception):
    if isinstance(error, app_commands.MissingPermissions):
        await inter.response.send_message("Você não tem permissão para executar esse comando.", ephemeral=True)
    elif isinstance(error, app_commands.CommandInvokeError):
        print("Error:", error)
        await inter.response.send_message("Um erro ocorreu.", ephemeral=True)
        raise error  # You can also log the error for debugging purposes.
    else:
        print("Error:", error)
        await inter.response.send_message(f"Erro: {str(error)}", ephemeral=True)
        raise error


async def main():
    async with client:
        await client.start(os.getenv("TOKEN"))

asyncio.run(main())