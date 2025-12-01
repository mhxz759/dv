#!/usr/bin/env python3
# -- coding: utf-8 --
"""
Bot para login de usuário e envio automático para grupos
"""

import asyncio
import logging
import re
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
import os
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BANNED_GROUPS = ['𝙄𝙉𝙁𝙊𝙎 𝙈𝙃𝙓𝙕', '𝑴𝒉𝒙𝒛 𝑹𝒆𝒇𝒆𝒓𝒆̂𝒏𝒄𝒊𝒂𝒔', 'BLUE POWER DONATES 𝗖𝗛𝗔𝗧 #𝟬1']

class UserBot:
    def __init__(self):
        self.client = None
        self.session_file = 'userbot_session'
        self.config_file = 'userbot_config.json'
        self.admin_groups = []
        self.forward_link = None  # link de encaminhamento

    async def setup_client(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                api_id = config.get('api_id')
                api_hash = config.get('api_hash')
                phone = config.get('phone')
        else:
            print("🔐 Configuração do UserBot")
            api_id = input("Digite seu API ID: ").strip()
            api_hash = input("Digite seu API Hash: ").strip()
            phone = input("Digite seu telefone (com código do país, ex: +5511999999999): ").strip()

            config = {'api_id': api_id, 'api_hash': api_hash, 'phone': phone}
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

        try:
            self.client = TelegramClient(self.session_file, int(api_id), api_hash)
            await self.client.start(phone=phone)
            logger.info("Cliente conectado com sucesso!")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False

    async def find_admin_groups(self):
        if not self.client:
            return []

        print("🔍 Procurando grupos onde você é administrador...")
        admin_groups = []

        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, (Channel, Chat)) and entity.title.lower() not in (group.lower() for group in BANNED_GROUPS):
                try:
                    if isinstance(entity, Channel):
                        if entity.megagroup or entity.broadcast:
                            me = await self.client.get_me()
                            participant = await self.client(GetParticipantRequest(
                                channel=entity, participant=me.id))
                            if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                                admin_groups.append({
                                    'id': entity.id,
                                    'title': entity.title,
                                    'type': 'supergroup' if entity.megagroup else 'channel',
                                    'members': entity.participants_count or 0
                                })
                                print(f"✅ {entity.title} - {entity.participants_count or 0} membros")
                    elif isinstance(entity, Chat):
                        if entity.admin_rights or entity.creator:
                            admin_groups.append({
                                'id': entity.id,
                                'title': entity.title,
                                'type': 'group',
                                'members': entity.participants_count or 0
                            })
                            print(f"✅ {entity.title} - {entity.participants_count or 0} membros")
                except:
                    continue

        self.admin_groups = admin_groups
        print(f"\n📊 Total de grupos encontrados: {len(admin_groups)}")
        return admin_groups

    def parse_message_link(self, link):
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

    async def forward_message_to_groups(self, source_chat, message_id):
        if not self.admin_groups:
            print("❌ Nenhum grupo de admin encontrado!")
            return

        message = await self.client.get_messages(source_chat, ids=message_id)
        if not message:
            print("❌ Mensagem não encontrada!")
            return

        print(f"📤 Encaminhando mensagem para {len(self.admin_groups)} grupos...")

        for group in self.admin_groups:
            try:
                await self.client.forward_messages(
                    entity=group['id'],
                    messages=message,
                    from_peer=source_chat
                )
                print(f"✅ Enviado para: {group['title']}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"❌ Erro em {group['title']}: {e}")

    async def loop_automatic_forward(self):
        if not self.forward_link:
            link = input("Cole o link da mensagem a ser encaminhada: ").strip()
            self.forward_link = link

        chat_id, message_id = self.parse_message_link(self.forward_link)
        if not chat_id or not message_id:
            print("❌ Link inválido!")
            return

        print("🔁 Iniciando envio automático a cada 50 minutos...")
        while True:
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Enviando...")
            await self.forward_message_to_groups(chat_id, message_id)
            print("⌛ Aguardando 50 minutos...")
            await asyncio.sleep(50 * 60)

    async def interactive_menu(self):
        while True:
            print("\n" + "="*50)
            print("🤖 UserBot - Menu Principal")
            print("="*50)
            print("1. 🔍 Buscar grupos de admin")
            print("2. 📤 Enviar mensagem para todos os grupos")
            print("3. 📋 Listar grupos encontrados")
            print("4. ⚙ Reconfigurar credenciais")
            print("5. 🚪 Sair")
            print("6. 🔁 Iniciar envio automático a cada 50 minutos")

            choice = input("Escolha uma opção: ").strip()

            if choice == "1":
                await self.find_admin_groups()
            elif choice == "2":
                print("Função desativada neste modo. Use envio automático (opção 6).")
            elif choice == "3":
                if self.admin_groups:
                    for i, group in enumerate(self.admin_groups, 1):
                        print(f"{i}. {group['title']} ({group['type']}) - {group['members']} membros")
                else:
                    print("❌ Nenhum grupo encontrado. Use a opção 1 primeiro.")
            elif choice == "4":
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
                if os.path.exists(f"{self.session_file}.session"):
                    os.remove(f"{self.session_file}.session")
                print("✅ Configurações removidas. Reinicie o bot.")
                break
            elif choice == "5":
                print("👋 Saindo...")
                break
            elif choice == "6":
                if not self.admin_groups:
                    await self.find_admin_groups()
                await self.loop_automatic_forward()
            else:
                print("❌ Opção inválida!")

    async def start(self):
        print("🚀 Iniciando UserBot...")
        if not await self.setup_client():
            print("❌ Falha ao conectar.")
            return
        await self.find_admin_groups()
        await self.interactive_menu()
        if self.client:
            await self.client.disconnect()

async def main():
    bot = UserBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
