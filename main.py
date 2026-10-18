from telethon import TelegramClient, events
import asyncio, threading, os, glob
from flask import Flask
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaWebPage

API_ID = int(os.environ.get("API_ID", "32695956"))
API_HASH = os.environ.get("API_HASH", "8d939c8130ea03c01cd9abe6a6e83d7a")
SESSION = os.environ.get("SESSION_STRING", "")
GRUPO = int(os.environ.get("GRUPO_DESTINO", "-1003764262854"))
TOPIC = int(os.environ.get("TOPIC_ID", "781555"))
CANAL = os.environ.get("CANAL_ORIGEN", "https://t.me/Horny_J")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot vivo"

threading.Thread(
    target=lambda: app.run(host='0.0.0.0', port=10000),
    daemon=True
).start()

if SESSION:
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
else:
    s = glob.glob("*.session")
    client = TelegramClient(
        s[0].replace('.session', '') if s else 'sesion_nube',
        API_ID,
        API_HASH
    )

async def cargar_progreso():
    try:
        async for m in client.iter_messages('me', limit=20):
            if m.text and m.text.startswith("PROGRESO_BOT:"):
                return int(m.text.split(":")[1].strip())
    except Exception as e:
        print(f"No se pudo cargar progreso: {e}")

    return 0

async def guardar_progreso(last_id):
    try:
        async for m in client.iter_messages('me', limit=20):
            if m.text and m.text.startswith("PROGRESO_BOT:"):
                await m.delete()

        await client.send_message(
            'me',
            f"PROGRESO_BOT:{last_id}"
        )

    except Exception as e:
        print(f"Error guardando progreso: {e}")

async def copiar_mensaje(m, destino):

    # Si es una vista previa web solamente
    if isinstance(m.media, MessageMediaWebPage):
        if m.text:
            await client.send_message(
                destino,
                m.text,
                reply_to=TOPIC
            )
        return True

    if m.media:
        await client.send_file(
            destino,
            m.media,
            caption=m.text,
            reply_to=TOPIC
        )
    else:
        await client.send_message(
            destino,
            m.text,
            reply_to=TOPIC
        )

    return True

async def main():

    await client.start()
    print("CLIENTE CONECTADO OK")

    origen = await client.get_entity(CANAL)
    destino = await client.get_entity(GRUPO)

    last_id = await cargar_progreso()

    print(f"ARRANCO DESDE: {last_id}")

    async for m in client.iter_messages(
        origen,
        min_id=last_id,
        reverse=True
    ):

        if not (m.media or m.text):
            last_id = m.id
            continue

        errores = 0

        while True:

            try:

                await copiar_mensaje(m, destino)

                print(f"Copiado {m.id}")

                last_id = m.id

                await guardar_progreso(last_id)

                await asyncio.sleep(1.5)

                break

            except FloodWaitError as e:

                print(
                    f"FLOODWAIT en {m.id} "
                    f"- Esperando {e.seconds} segundos "
                    f"y reintentando..."
                )

                await asyncio.sleep(e.seconds + 10)

                continue

            except Exception as e:

                errores += 1

                print(
                    f"Error #{errores} en mensaje {m.id}: {e}"
                )

                print(
                    "Reintentando el mismo mensaje dentro de 10 segundos..."
                )

                await asyncio.sleep(10)

                continue

    print("HISTORIAL LISTO - EN VIVO")

    @client.on(events.NewMessage(chats=CANAL))
    async def handler(event):

        while True:

            try:

                if not (
                    event.message.media
                    or
                    event.message.text
                ):
                    return
await copiar_mensaje(
                    event.message,
                    destino
                )

                await guardar_progreso(
                    event.message.id
                )

                break

            except FloodWaitError as fw:

                print(
                    f"FloodWait en vivo: "
                    f"{fw.seconds} segundos"
                )

                await asyncio.sleep(
                    fw.seconds + 5
                )

            except Exception as ex:

                print(
                    f"Error en vivo: {ex}"
                )

                print(
                    "Reintentando en 10 segundos..."
                )

                await asyncio.sleep(10)

    await client.run_until_disconnected()

asyncio.run(main())
