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

# Crear una instancia del cliente
bot = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

admin = os.environ["admin"]
MB = 1024 * 1024




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
        
    os.remove(ruta_adjunto)
    return "OK"


    


def dividir(user_id , archivo_zip, nombre_archivo, chunks=chunks, carpeta_destino=os.path.abspath(os.path.join(".", "media"))):
    
    
    with open(archivo_zip, "rb") as archivo:
        archivo.seek(0)
                
        for i in range(int(os.path.getsize(archivo_zip) / (MB * chunks)) + 1):
            dic_temp[user_id] = os.path.join(carpeta_destino, "part_" + nombre_archivo + f".{i+1:03}")
                                   
            with open(dic_temp[user_id], "wb") as file_part:
                file_part.write(archivo.read(chunks * MB))
            
            enviar_correo_con_adjunto("reinier.mayea@nauta.cu", "Archivo Solicitado", f"Parte {i + 1} de {int(len(archivo_zip) / MB) + 1}", dic_temp[user_id], EMAIL_USER, EMAIL_PASS)
            
            os.remove(dic_temp[user_id])
            
    os.remove(archivo_zip)




@bot.on_message((filters.video | filters.audio | filters.document | filters.all) & ~ filters.text)
async def recibir(cliente, message):
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
    
    await message.download(path)
    await bot.send_message(message.chat.id, "El archivo ya se descargó :)")
    
    #si el archivo es más grande que el maximo de partes:
    if os.path.getsize(path) > chunks * MB:
        
        await bot.send_message(message.chat.id, "El archivo ya se descargó :) Ahora lo voy a enviar por partes de 15 mb")
        
        with ZipFile(os.path.join(".", "media", f"{os.path.basename(path)}.zip"), "w") as file:
            file.write(path, os.path.basename(path))
            
        
        dividir(message.chat.id, os.path.join(".", "media", f"{os.path.basename(path)}.zip"), nombre)    
    
    else:
        enviar_correo_con_adjunto("reinier.mayea@nauta.cu", "Archivo Solicitado", nombre , path, "reimahopper@gmail.com", "exyw bmjs fuuo bkxy")
        
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
        
bot.run()