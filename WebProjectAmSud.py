import wptools
import re
import sqlite3
import json
from zipfile import ZipFile

def get_info(country):           # Pour obtenir les informations de Wikipédia
    try:
        page = wptools.page(country)
        page.get_parse(False)
        return page.data['infobox']
    except:
        print('No such country,please check your input')
        return None

def print_capital(info):        # Pour imprimer le nom du pays, la capitale,
                                # et ses coordonnées géographiques 
    try:                        # en cas où ce pays n'a pas de capital
        print (get_name(info),get_capital(info),get_coords(info))
    except:
        print('')

def get_name(info):
    try:
        nom = re.match('[a-z|A-Z| |-]*',info['conventional_long_name'])   
        return nom[0]
    except:
        print('no conventional long name') # conventional_long_name n'existe pas
    return f''

def get_capital(info):
    try:
        cap = info['capital']
        m = re.findall('\[\[(.*)\]\]',cap)[0]
        m = re.match('[\w+ ]*',m)[0]
        return m
    except:
        return f""
    
def get_coords(info):
    coor_get = info['coordinates']
    coor = {'lat':"",'lon':""}
    m = re.findall('Coord(.*)type',coor_get)[0]
    sign = re.findall('[A-Z]',m)
    num = re.split('[A-Z]',m)
    lat = re.findall('\d+',num[0])
    lon = re.findall('\d+',num[1])
    lat = float(lat[0]) + (float(lat[1])/60 if len(lat)==2 else 0) + (float(lat[2])/3600 if len(lat)==3 else 0)
    lon = float(lon[0]) + (float(lon[1])/60 if len(lon)==2 else 0) + (float(lon[2])/3600 if len(lon)==3 else 0)
    if sign[0]=='S':        # S: négatif
        lat = -lat
    if sign[1]=='W':        # W: négatif
        lon = -lon
    coor['lat'] = lat
    coor['lon'] = lon
    return coor

def save_country(conn,country,info):
     c = conn.cursor()
     try:
         sql = 'INSERT INTO countries VALUES (?, ?, ?, ?, ?)'
         # les infos à enregistrer
         name = get_name(info)
         capital = get_capital(info)
         coords = get_coords(info)
         # soumission de la commande (noter que le second argument est un tuple)
         c.execute(sql,(country,name, capital, coords['lat'],coords['lon']))
     except Exception as e:
         if str(e) == 'UNIQUE constraint failed: countries.wp':
             # ce pays a été déjà enregistré
             print('You have already saved',name)
     conn.commit()
    
def delete_country(conn,country):
    c = conn.cursor()
    sql = 'DELETE from countries where wp="'+ str(country)+'";'
    c.execute(sql)
    conn.commit()

def read_country(conn,country):
    c = conn.cursor()
    try:
        sql = 'select * from countries'
        info = c.execute(sql)
        conn.commit()
        return (list(info))     # de type liste
    except:
        return None
    
def save_info_zip(file):
    # ouverture d'une connexion avec la base de données
    conn = sqlite3.connect('pays.sqlite')
    with ZipFile(file+'.zip','r') as z: # liste des documents contenus dans le fichier zip
        for c in z.namelist():   
            info = json.loads(z.read(c))    # infobox de l'un des pays
            country = c.split('.')[0]
            save_country(conn,str(country),info)
            
def delete_info_zip(file):
    # ouverture d'une connexion avec la base de données
    conn = sqlite3.connect('pays.sqlite')
    with ZipFile(file+'.zip','r') as z: # liste des documents contenus dans le fichier zip
        for c in z.namelist():   
            country = c.split('.')[0]
            delete_country(conn,str(country))
            
save_info_zip('south_america')
delete_info_zip('south_america')
