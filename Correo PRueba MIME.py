from pyrogram import Client, filters
import os

# Configuración del bot
api_id = os.environ["api_id"]  # Reemplaza con tu API ID
api_hash = os.environ["api_hash"]  # Reemplaza con tu API Hash
bot_token = os.environ["token"]  # Reemplaza con el token de tu bot

# Crear una instancia del cliente
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Ruta donde se guardarán los archivos descargados
DOWNLOAD_PATH = "downloads/"

# Crear la carpeta de descargas si no existe
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# Manejador de mensajes que contienen archivos
@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def download_file(client, message):
    # Obtener el nombre del archivo
    if message.document:
        file_name = message.document.file_name
    elif message.video:
        file_name = message.video.file_name
    elif message.audio:
        file_name = message.audio.file_name
    elif message.photo:
        file_name = f"photo_{message.photo.file_id}.jpg"
    
    # Ruta completa donde se guardará el archivo
    file_path = os.path.join(DOWNLOAD_PATH, file_name)
    
    # Descargar el archivo
    try:
        await message.download(file_path)
        
    except:
        await app.send_message("Ha ocurrido un error")
        return
        
    try:
        os.path.getsize(file_name)
    
    except:
        await app.send_message("Ha ocurrido un error")
        return
    
    
    await app.send_document(message.chat.id, file_name)
    
    
    # Enviar un mensaje de confirmación
    await message.reply_text(f"Archivo '{file_name}' descargado con éxito.")

# Iniciar el bot
app.run()