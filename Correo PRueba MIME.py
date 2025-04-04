import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import pyrogram
from pyrogram import Client, filters
import os
import subprocess
from zipfile import ZipFile
from flask import Flask, request
import threading
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
if not "media" in os.listdir():
    os.mkdir("media")
    
dic_temp = {}
chunks = 15

# Configuración del bot
api_id = os.environ["api_id"]  # Reemplaza con tu API ID
api_hash = os.environ["api_hash"]
bot_token = os.environ["token"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_TARGET = os.environ["EMAIL_TARGET"]

# Crear una instancia del cliente
bot = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token, parse_mode=pyrogram.enums.ParseMode.HTML)


admin = int(os.environ["admin"])
MB = 1024 * 1024




def download_progress(current, total, bot, message, nombre, edit):
    # print("Descargado: " + str(round(100 / (total / current))) + "%")
    no_guardado="⬜"
    guardado = "⬛"
    try:
        bot.edit_message_text(message.chat.id, edit.id, f"Descargando <b>{nombre}</b>\n\nProgreso de Descarga:\n|{guardado * (round(100 / (total / current)) // 10)}{no_guardado * (10 - (round(100 / (total / current)) // 10))}| {str(round(100 / (total / current)))}%")
        
    except Exception as e:
        bot.delete_messages(message.chat.id, edit.id)
        if "MESSAGE_NOT_MODIFIED" in str(e.args):
            pass
        else:
            bot.send_message(message.chat.id, "No se pudo descargar adecuadamente :(")
    
    return
    
def enviar_correo_con_adjunto(destinatario, asunto, cuerpo, ruta_adjunto, remitente_email, remitente_password):
    
    """
    Envía un correo electrónico con un archivo adjunto.

    Args:
        destinatario (str): Dirección de correo del destinatario.
        asunto (str): Asunto del correo electrónico.
        cuerpo (str): Cuerpo del mensaje del correo electrónico.
        ruta_adjunto (str): Ruta completa al archivo adjunto.
        remitente_email (str): Dirección de correo del remitente (tu correo).
        remitente_password (str): Contraseña de correo del remitente.
    """
    

    # 1. Crear el mensaje MIME
    # Crea un objeto MIMEMultipart: Es necesario para enviar un correo con adjuntos.
    # Añade los encabezados del mensaje: Remitente, destinatario y asunto.
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente_email
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    
    
    # 2. Agregar el cuerpo del correo
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # 3. Agregar el archivo adjunto
    try:
        with open(ruta_adjunto, "rb") as archivo_adjunto:
            nombre_archivo = os.path.basename(ruta_adjunto)
            adjunto = MIMEApplication(archivo_adjunto.read(), Name=nombre_archivo)
            adjunto['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
            mensaje.attach(adjunto)

    except FileNotFoundError:
        os.remove(ruta_adjunto)
        return ("Error", "No se encontró el archivo")
        

    except Exception as e:
       print(f"Ocurrió un error al adjuntar el archivo: {e}")
       os.remove(ruta_adjunto)
       return ("Error", e.args)

    # 4. Conectarse al servidor SMTP y enviar el correo
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:  # Utiliza el servidor SMTP de Gmail
            servidor.starttls()  # Iniciar TLS (seguridad)
            servidor.login(remitente_email, remitente_password)  # Iniciar sesión en el correo
            servidor.send_message(mensaje)  # Enviar el correo
            print("Correo enviado con éxito.")
    except Exception as e:
        os.remove(ruta_adjunto)
        return ("Error", e.args)
        
    return "OK"


    


def dividir(user_id , archivo_zip, nombre_archivo, chunks=chunks, carpeta_destino=os.path.abspath(os.path.join(".", "media"))):
    
    
    with open(archivo_zip, "rb") as archivo:
        archivo.seek(0)
        for i in range(int(os.path.getsize(archivo_zip) / (MB * chunks)) + 1):
            dic_temp[user_id] = os.path.join(carpeta_destino, "part_" + nombre_archivo + f".{i+1:03}")
                                   
            with open(dic_temp[user_id], "wb") as file_part:
                file_part.write(archivo.read(chunks * MB))
            
            res = enviar_correo_con_adjunto(EMAIL_TARGET, "Archivo Solicitado", f"Parte {i + 1} de {int(os.path.getsize(archivo_zip) / (MB * chunks)) + 1}", dic_temp[user_id], EMAIL_USER, EMAIL_PASS)
            
            if isinstance(res, tuple):
                return
            
            os.remove(dic_temp[user_id])
            
    os.remove(archivo_zip)


@bot.on_message(filters.regex("/enviar"))
def cmd_enviar(cliente, message):
    if len(message.text.split("_")) > 1:
        dividir(
            message.chat.id,
            #direccion del archivo zip
            os.path.abspath(os.path.join(".", "media", os.listdir(os.path.join(".", "media"))[int(message.text.split("_")[-1])])),
            #nombre de archivo 
            os.path.basename(os.path.join(".", "media", os.listdir(os.path.join(".", "media"))[int(message.text.split("_")[-1])])).replace(re.search(r"[.].*", os.path.basename(os.path.join(".", "media", os.listdir(os.path.join(".", "media"))[int(message.text.split("_")[-1])]))).group(), ""))

@bot.on_message((filters.video | filters.audio | filters.document | filters.all) & ~ filters.text)
async def recibir(cliente, message):
    
    await bot.send_message(message.chat.id, "Ahora procederé a descargar el archivo enviado:)")
    dic_temp[message.chat.id] = ""
       
    if message.document:
        nombre = message.document.file_name
    elif message.photo:
        nombre = f"{message.photo.file_id}.jpg"
    
    elif message.video:
        nombre = message.video.file_name
        
    elif message.audio:
        nombre = message.audio.file_name
        
        
    path = os.path.join(os.path.abspath("."), "media" , nombre)
    
    msg = await bot.send_message(message.chat.id, "Inciando Descarga...")
    
    try:
        await bot.download_media(message, path, progress=download_progress, progress_args=(bot, message, nombre, msg))
    except Exception as err:
        bot.send_message(message.chat.id, f"Ha ocurrido un error intentando descargar el archivo:\n\n{err.args}")
        return
    
    
    #si el archivo es más grande que el maximo de partes:
    try:
       os.path.getsize(path) 
    except:
        await bot.send_message(message.chat.id, "Ha ocurrido un error, el archivo no se descargó :(")
        return
    
    
    
    await bot.send_message(message.chat.id, f"El archivo {nombre} ya se descargó :)")
    
    
    if os.path.getsize(path) > (chunks * MB):
        
        
        with ZipFile(os.path.join(".", "media", f"{os.path.basename(path)}.zip"), "w") as file:
            file.write(path, os.path.basename(path))
            
            for e, direct in enumerate(os.listdir(os.path.dirname(path))):
                if direct == file.filename:
                    await bot.send_message(message.chat.id, f"El archivo ya se descargó :)\n\nAL parecer el archivo es mayor a {chunks} MB, utiliza el comando /enviar_{e} para enviarlo al correo ({EMAIL_TARGET}) dividido")    
            else:
                await bot.send_message(message.chat.id, f"El archivo ya se descargó :)\n\nAL parecer el archivo es mayor a {chunks} MB, utiliza el comando /enviar_<índice> para enviarlo al correo dividido")    
                    
        
        
        # dividir(message.chat.id, os.path.join(".", "media", f"{os.path.basename(path)}.zip"), nombre)    
        
        os.remove(path)
    
    else:
        enviar_correo_con_adjunto(EMAIL_TARGET, "Archivo Solicitado", nombre , path, EMAIL_USER, EMAIL_PASS)
        
        await bot.send_message(message.chat.id, "El archivo ya se descargó y fué enviado al correo :)")
    
    
@bot.on_message(filters=filters.command(["c"]) & filters.user(1413725506))
def c(bot, message):
    try:
        dic_temp[message.from_user.id] = {"comando": False, "res": False, "texto": ""}
        dic_temp[message.from_user.id]["comando"] = message.text.split()
        if len(dic_temp[message.from_user.id]["comando"]) == 1:
            bot.send_message(1413725506, "No has ingresado nada")
            return
        
        dic_temp[message.from_user.id]["comando"] = " ".join(dic_temp[message.from_user.id]["comando"][1:len(dic_temp[message.from_user.id]["comando"])])
        
        dic_temp[message.from_user.id]["res"] = subprocess.run(dic_temp[message.from_user.id]["comando"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        
        if dic_temp[message.from_user.id]["res"].returncode:
            dic_temp[message.from_user.id]["texto"]+= "❌ Ha ocurrido un error usando el comando...\n\n"
        
        if dic_temp[message.from_user.id]["res"].stderr:
            dic_temp[message.from_user.id]["texto"]+= f"stderr:\n{dic_temp[message.from_user.id]["res"].stderr}\n\n"
            
        if dic_temp[message.from_user.id]["res"].stdout:
            dic_temp[message.from_user.id]["texto"]+= f"stdout\n{dic_temp[message.from_user.id]["res"].stdout}\n\n"
            
            
        try:
            bot.send_message(1413725506, dic_temp[message.from_user.id]["texto"])
        except:
            with open("archivo.txt", "w") as file:
                file.write(dic_temp[message.from_user.id]["texto"])
            
            with open("archivo.txt", "rb") as file:
                bot.send_document(message.chat.id, os.path.abspath(file.name))
                
            os.remove("archivo.txt")
                
    
    except Exception as e:
        bot.send_message(1413725506, f"Error:\n{e.args}")
    
    return

        
@bot.on_message(filters.text)
async def cmd_texto(cliente, message):
    await bot.send_message(message.chat.id, "Tienes que escribir algo Mastodonte")
        


# app = Flask(__name__)        

# @app.route("/")
# def cmd_flask():
#     return "Hello World"
        
        
# def flask_run():
#     try:
#         app.run("0.0.0.0", port=os.environ["PORT"])
#     except:
#         app.run("0.0.0.0", port=5000)

# threading.Thread(name="hilo_flask", target=flask_run).start()

bot.run()
