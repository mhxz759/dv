from telethon import TelegramClient
import asyncio
import logging
import re

# ===============================
# CONFIGURAÇÕES DO TELEGRAM
# ===============================
API_ID = 22587635
API_HASH = "7fe3acd96c338b764717c1d493fe540d"
SESSION_NAME = "jk"

# ===============================
# CONFIGURAÇÃO DA DIVULGAÇÃO
# ===============================
DIVULGACAO_LINK = "https://t.me/c/2571183210/2140"
INTERVALO_MINUTOS = 50  # envio a cada 50 minutos

# ===============================
# LOGGING
# ===============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_message_link(link):
    """Transforma link do Telegram em chat_id e message_id"""
    patterns = [
        r't\.me/c/(-?\d+)/(\d+)',
        r't\.me/([^/]+)/(\d+)',
        r'telegram\.me/c/(-?\d+)/(\d+)',
        r'telegram\.me/([^/]+)/(\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            chat_identifier = match.group(1)
            message_id = int(match.group(2))
            chat_id = int(f"-100{chat_identifier}") if chat_identifier.isdigit() else chat_identifier
            return chat_id, message_id
    return None, None


async def divulgar_loop(client):
    """Envia a mensagem para todos os chats que você administra a cada INTERVALO_MINUTOS"""
    chat_id, message_id = parse_message_link(DIVULGACAO_LINK)
    if not chat_id or not message_id:
        logger.error("Link de divulgação inválido!")
        return

    # Obtém lista de grupos administrados
    admin_groups = []
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if hasattr(entity, "megagroup") or hasattr(entity, "creator"):
            admin_groups.append(entity)

    if not admin_groups:
        logger.warning("Nenhum grupo de admin encontrado. Encerrando.")
        return

    logger.info(f"Encontrados {len(admin_groups)} grupos de admin para envio.")

    while True:
        logger.info("Iniciando envio da divulgação...")
        for group in admin_groups:
            try:
                await client.forward_messages(
                    entity=group.id,
                    messages=message_id,
                    from_peer=chat_id
                )
                logger.info(f"✅ Enviado para: {group.title}")
                await asyncio.sleep(1)  # evita flood
            except Exception as e:
                logger.error(f"❌ Erro ao enviar para {getattr(group, 'title', group.id)}: {e}")

        logger.info(f"⌛ Aguardando {INTERVALO_MINUTOS} minutos para próximo envio...")
        await asyncio.sleep(INTERVALO_MINUTOS * 60)


async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    logger.info("Iniciando sessão...")
    await client.start()
    logger.info("Sessão iniciada com sucesso!")

    await divulgar_loop(client)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
