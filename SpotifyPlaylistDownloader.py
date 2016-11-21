#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   SpotifyPlaylistDownlaoder
#
#   Fecha última modificación: 15/08/2016
#
#   Este archivo se puede usar como API, usando las funciones que este archivo incluye, o como un programa en si mismo, ejecutándolo.
#   Se necesitan módulos externos a los incluidos en Python 2.7: mutagen, requests, pafy y youtube-dl. El programa tiene una función para
#   instalarlos automáticamente, pero no se recomienda, ya que se basa en pip-install y este puede instalar versiones antiguas, provocando
#   errores. Los enlaces de los módulos para la instalación manual son los siguientes:
#
#   mutagen: https://pypi.python.org/pypi/mutagen
#   pafy: https://pypi.python.org/pypi/pafy
#   requests: https://github.com/kennethreitz/requests
#   youtube-dl: https://rg3.github.io/youtube-dl/download.html
#
#   Este programa usa la API de Spotify. Las credenciales usadas no son permanentes, así que si alguna vez caducan se debe crear una nueva aplicación
#   en la API de Spotify y copiar la ID del cliente y la clave secreta del cliente en las variables CLIENT_ID y CLIENT_SECRET respectivamente.
#
#   Probado en Ubuntu y en Windows 7/10
#
#   Donaciones: 17ZkyN5Zb4ZzcMi8m9NXdL7Tc25xFsW5C5
#

import json
import time
import sys
import os
import re
import random
import string
import ctypes
import urllib

try:
    from mutagen.mp4 import MP4
    from mutagen.mp4 import MP4Cover
    import requests
    import pafy
    run_instalador = False
except ImportError as e:
    print u"[ERROR] Error al importar módulos: (%s). Ejecutando instalador." % str(e)
    run_instalador = True

######################
# VARIABLES GLOBALES #
######################

USUARIO = "" #Usuario por defecto, dejar en blanco para intorudcirlo al abrir el programa.
SRCH_ALBUM = True #Buscar imagen y año del albúm
DESCARGAR_MP4 = True #Descargar en formato MP4 en vez de M4A, para convertir más fácilmente a MP3.

#Variables de la API de Spotify
CLIENT_ID = ""
CLIENT_SECRET = ""

def INSTALADOR():
    """
    Instalar las librerías externas necesarias para el uso de este programa. Se recomienda usar esta función como última opción.
    """
    m = ["mutagen", "requests", "pafy", "youtube-dl"]
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    print u"[INFO] Se instalarán las dependencias. Se podrían instalar versiones antiguas, así que se recomienda instalar 'mutagen','requests', 'pafy' y 'youtube-dl' manualmente para evitar futuros errores."
    if not is_admin:
        print u"[WARN] El programa no tiene derechos de administrador. Se recomienda reabrirlo con dichos derechos. Se puede probar a instalar igualmente"
    raw_input("Pulse ENTER para continuar")
    try:
        import pip
    except ImportError:
        print u"[ERROR] Error al instalar las librerías externas. Puede probar a instalar la librería 'pip' y volver a ejecutar este instalador o instalar manualmente las siguientes dependencias: "
        for i in m: print i
        raw_input()
        sys.exit(1)
    for i in m:
        print "[INFO] Instalando '%s'" % i
        if pip.main(['install', i]):
            print u"[ERROR] Error al instalar las librerías externas. Deberá instalarlas manualmente. En el código fuente de este programa hay más información. "
            raw_input()
            sys.exit(1)
    print u"[INFO] Comprobando dependencias..."
    for i in m:
        try:
            if i == "youtube-dl": continue
            test = __import__(i)
        except ImportError as e:
            print u"[ERROR] Error al instalar las librerías externas: (%s). Deberá instalarlas manualmente. En el código fuente de este programa hay más información." %str(e)
            raw_input()
            sys.exit(1)
    raw_input("[INFO] Dependencias instaladas correctamente! Reinicie el programa.")
    sys.exit(1)

if(run_instalador): INSTALADOR()
if(DESCARGAR_MP4):
    extension_archivo = "mp4"
else:
    extension_archivo = ".m4a"

def FiltrarASCII(texto):
    "Devuelve el texto sólo con los carácteres imprimibles en pantalla."
    return filter(lambda x: x in set(string.printable), texto)
    
def printlog(msg):
    "Imprime el mensaje con fecha, hora, minutos y segundos"
    date = time.strftime("%d/%m/%Y %H:%M:%S")
    try:
        print u'[%s] %s' % (date, msg)
    except UnicodeEncodeError:
        text = '[%s] %s' % (date, msg)
        print FiltrarASCII(text)
    except UnicodeDecodeError:
        text = '[%s] %s' % (date, msg)
        print FiltrarASCII(text)

token = 0
def ObtenerToken(idd,secret):
    """
    Obtiene el token Bearer de la API de Spotify. 
    Parámetros:
        - idd (str): id del cliente de la API de Spotify
        - secret (str): clave privada del cliente de la API de Spotify.
    Devuelve:
        - token (str)
    """
    token_url = "https://accounts.spotify.com/api/token"
    token_body = {"grant_type":"client_credentials"}
    try:
        token_response = requests.post(token_url, data=token_body, auth=(idd, secret))
    except requests.exceptions.ConnectionError:
        printlog("[ERROR] ENo se ha detectado conexion a Internet.")
        raw_input()
        sys.exit(0)
    if token_response.status_code == 200:
        decode = json.loads(token_response.text)
        return decode['access_token'] #Tipo por defecto: bearer
    else:
        printlog("[ERROR] Error al conectar con la API de Spotify. Se deben cambiar las claves.")
        raw_input()
        sys.exit(0)
        
def ObtenerPlaylists(usuario, token2):
    """
    Obtiene un límite de 50 playlist públicas de un usuario. 
    Parámetros:
        - usuario (str): usuario de Spotify. Debe ser la última parte de la URI de Spotify, ejemplo: spotify:user:usuario, sólo usuario.
        - token2 (str): token de la API.
    Devuelve:
        - lista con todas las playlist en formato JSON
    """
    pl_request_url = "https://api.spotify.com/v1/users/%s/playlists/?limit=50" % usuario
    pl_request = requests.get(pl_request_url, headers={"Authorization":"Bearer "+token2})
    if pl_request.status_code == 200:
        decode = json.loads(pl_request.text)
        if decode["total"] > 49:
            printlog("[ERROR] No se pueden exceder las 50 playlists")
            raw_input()
            sys.exit(0)
        return decode["items"]
    else:
        return 0
        
def ObtenerAlbum(album):
    """
    Obtiene la fecha de salida de un álbum y su imagen. Se basa en la API de Spotify.
    Parámetros:
        - album (str): id del album en Spotify.
    Devuelve:
        - año (str), canciones totales del album (int), Link del Album Art (str)
    """
    if SRCH_ALBUM:
        album_request_url = "https://api.spotify.com/v1/albums/" + album
        album_request = requests.get(album_request_url)
    else:
        return "", 0, ""
    if album_request.status_code == 200:
        decode = json.loads(album_request.text)
        fecha = decode["release_date"]
        url_album = decode["images"][0]["url"]
        return fecha.split("-")[0], decode['tracks']['total'], url_album #Nomes el any i les cancons totals
    else:
        return "", 0, ""
        
def CancionesPlaylist(playlist_link, token2):
    """
    Obtiene las canciones de una playlist.
    Parámetros:
        - Playlist link (str): link de la playlist
        - token (str): token de la API
    Devuelve:
        - Lista (1 elemento): ["Artista - Nombre Canción"]
        - Lista (8 elementos): [Nombre, Artista, Album, Tracknumber(int), Albumyear, Tracktotal (int), Link Album, Duracion(int)]
    """
    canciones_raw = []
    canciones_info = [] #[Nombre, Artista, Album, Tracknumber(int), Albumyear, Tracktotal (int), Link Album, Duracion(int), LinkYoutube]
    while True:
        pl_request = requests.get(playlist_link, headers={"Authorization":"Bearer "+token2})
        decode = json.loads(pl_request.text)
        for cancion in decode["items"]:
            artista = cancion['track']['artists'][0]['name']
            nombre = cancion['track']['name']
            album = cancion['track']['album']['name']
            tracknumber = int(cancion['track']['track_number'])
            album_year, album_total, album_link = ObtenerAlbum(cancion['track']['album']['id'])
            duracion = cancion['track']['duration_ms']/1000
            nombre_completo = artista + " - " + nombre
            while nombre_completo in canciones_raw:
                nombre_completo = nombre_completo + " (r)" #Repetido
            canciones_raw.append(nombre_completo)
            canciones_info.append([nombre, artista, album, tracknumber, album_year, album_total, album_link, duracion])
        if decode['next'] == None:
            break
        else:
            playlist_link = decode['next']
    printlog("Playlist cargada. Canciones totales: %i/%i" % (len(canciones_raw), decode['total']))
    return canciones_raw, canciones_info
    
def EstablecerTags(archivo, lista_tags):
    """
    Recibe una lista con el formato [Nombre, Artista, Album, Tracknumber(int), Albumyear, Tracktotal (int), Link Album, Duracion, LinkYoutube]
    """
    tags_cancion = MP4(archivo)
    tags_cancion['\xa9nam'] = lista_tags[0]
    tags_cancion['\xa9ART'] = lista_tags[1]
    tags_cancion['\xa9grp'] = lista_tags[1]
    tags_cancion['\xa9alb'] = lista_tags[2]
    tags_cancion['trkn'] = [(lista_tags[3], lista_tags[5])]
    tags_cancion['\xa9day'] = lista_tags[4]
    tags_cancion['\xa9cmt'] = lista_tags[8]
    if not lista_tags[6]:
        fd = urllib.urlopen(lista_tags[6])
        tags_cancion['covr'] = [MP4Cover(fd.read(), MP4Cover.FORMAT_JPEG)]
        fd.close()
    tags_cancion.save()
    return 1
        
def ObtenerLink(nombre, audio_length):
    """
    Busca el enlace de una canción en YouTube. Comprueba la longitud del vídeo respecto a la de la canción original.
    La longitud descargada no puede ser superior a: (longitud_spotify + longitud_spotify * accuracy). Se recomienda un 10% = 0.1.
    """
    accuracy = 0.1
    i = 0
    while True:
        link = "https://youtube.com/results?search_query="+nombre
        link_request = requests.get(link)
        search_results = re.findall(r'href=\"\/watch\?v=(.{11})', link_request.text)
        provisional = "https://youtube.com/watch?v="+search_results[i]
        try:
            v = pafy.new(provisional)
            len_video = float(v.length)
        except TypeError:
            continue
        diferencia = abs(len_video/audio_length-1)
        if diferencia <= accuracy:
            return provisional
        i += 1
        if i == len(search_results):
            i = 0
            accuracy = accuracy + 0.1
    
def DescargarSonido(id, link):
    """
    Descarga un vídeo de Youtube. Devuelve el nombre del archivo.
    """
    v = pafy.new(link)
    extensiones = []
    for a in v.audiostreams:
        extensiones.append(a.extension)
    if "m4a" in extensiones:
        extension = "m4a"
    else:
        printlog("[ERROR] Conjunto de extensiones no soportadas!")
        raw_input()
        return 0
    path = id+"."+extension_archivo
    v.audiostreams[extensiones.index(extension)].download(quiet=True, filepath=path)
    return path

def main():
    print ""
    print "       ***************************************"
    print "       **                                   **"
    print "       **    Spotify Playlist Downloader    **"
    print "       **                                   **"
    print "       ***************************************"
    print ""
    global USUARIO
    if not USUARIO:
        USUARIO = raw_input("Usuario / URI de Spotify: ").replace("spotify:user:", "")
    if len(sys.argv) > 1:
        USUARIO = sys.argv[1].replace("spotify:user:", "")
    printlog("Accediendo a la API de Spotify")
    token = ObtenerToken(CLIENT_ID, CLIENT_SECRET)
    printlog("Obteniendo playlists de '%s'" % USUARIO)

    pl_todas = ObtenerPlaylists(USUARIO, token)
    printlog("Cargadas %i playists! Escoge la deseada: " % len(pl_todas))
    contador = 1
    for pl in pl_todas:
        print str(contador) + ". " + pl['name']
        contador += 1
    opcion = input("Playlist: ")

    t1 = time.time()
    pl_aim = pl_todas[opcion-1]
    printlog("Cargando Playlist '%s'..." % pl_aim['name'])
    pl_aim_url = pl_aim['tracks']['href']
    canciones_raw, canciones_info = CancionesPlaylist(pl_aim_url, token)

    dir = "musica%i/" % random.randint(0,1000)
    os.mkdir(dir)
    os.chdir(dir)
    for i in range(len(canciones_raw)):
        link_cancion = ObtenerLink(canciones_raw[i], canciones_info[i][7])
        canciones_info[i].append(link_cancion)
        new_name = canciones_raw[i]+"."+extension_archivo
        rx = "[" + re.escape(''.join([':', '*', '"', '?', '<', '>', '/', '\\'])) + "]"
        new_name = re.sub(rx, '', new_name)
        printlog('[%i/%i] Descargando "%s"' % (i+1, len(canciones_raw), new_name))
        try:
            archivo = DescargarSonido(str(i), link_cancion)
            EstablecerTags(archivo, canciones_info[i])
            os.rename(archivo, new_name)
        except WindowsError: #Error al cambiar el nom o crear l'arxiu
            printlog("Omitiendo archivo")
            new_name = FiltrarASCII(new_name)
            open("ommited.txt", "a").write(new_name+"\n")
        except TypeError:
            new_name = FiltrarASCII(new_name)
            printlog("Reintentando...")
            try:
                archivo = DescargarSonido(new_name, link_cancion)
                EstablecerTags(archivo, canciones_info[i])
            except:
                printlog("Omitiendo archivo")
                open("ommited.txt", "a").write(new_name+"\n")
        except KeyboardInterrupt:
            printlog("Descarga abortada. Pulse enter para salir!")
            raw_input()
            sys.exit(0)
        except:
            msg = "Unknown Error: " + str(sys.exc_info()[0])
            printlog(msg)
            new_name = FiltrarASCII(new_name)
            open("ommited.txt", "a").write(new_name+"\n")

    total_time = time.time() - t1
    printlog("Playlist descargada en %s (%i s)" % (dir, total_time))
    raw_input("Pulse enter para salir...")

if __name__ == "__main__":
    main()
