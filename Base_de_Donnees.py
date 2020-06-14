import wptools
import re
import sqlite3
import json
from zipfile import ZipFile

def get_info(country):
    from zipfile import ZipFile
    import json

    with ZipFile("oceania.zip","r") as z:
    
        # liste des documents contenus dans le fichier zip
        z.namelist()
    
        # infobox de l'un des pays
        info = json.loads(z.read(country+".json"))
        return info

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
    try :
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
    except :
        coor = {'lat':"",'lon':""}
        coor['lat'] = f""
        coor['lon'] = f""
        return coor

def get_currency(info):
    
    if info['common_name'] == 'Samoa':
        return 'Samoan Tala'
    else:
        cap = info['currency']
        m = re.findall('\[\[(.*)\]\]',cap)[0]
        l = m.split('|')
        return l[-1]
   
def get_area(info):
    try :
        area = info['area_km2']
        area = float(area.replace(",",""))
        return area
    except :
        return f""

def get_population(info):
    try :
        population = info['population_census']
        population = float(population.replace(",",""))
        return population
    except :
        try :
            population = info["population_estimate"]
            population = float(population.replace(",",""))
            return population
        except :
            return f""
    
def get_population_year(info):
    try :
        population_year = info['population_census_year']
        population_year = int(population_year.replace(",",""))
        return population_year
    except :
        try :
            population_year = info["population_estimate_year"]
            population_year = int(population_year.replace(",",""))
            return population_year
        except :
            return f""

def save_country(conn,country,info):
     c = conn.cursor()
     try:
         sql = 'INSERT INTO countries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
         # les infos à enregistrer
         name = get_name(info[0])
         capital = get_capital(info[0])
         coords = get_coords(info[0])
         area = get_area(info[0])
         population = get_population(info[0])
         population_year = get_population_year(info[0])
         continent = info[-1]
         flag = get_flag(info[1])
         currency = get_currency(info[0])
         link = "https://en.wikipedia.org/wiki/" + info[1].strip('.json')
         # soumission de la commande (noter que le second argument est un tuple)
         c.execute(sql,(country,name, capital, coords['lat'],coords['lon'],area,population,population_year, continent, flag,currency,link))
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
    
def save_info_zip(conn,file):
    with ZipFile(file+'.zip','r') as z: # liste des documents contenus dans le fichier zip
        for c in z.namelist():   
            info = [json.loads(z.read(c)),c,file]    # infobox de l'un des pays
            country = c.split('.')[0]
            save_country(conn,str(country),info)
            
    
def get_flag(name):
    with ZipFile('flags.zip','r') as z: 
        for c in z.namelist():
            if match_flags(name,c):
                return c
    
def match_flags(a,b):
    n=len(a)
    if a[0].lower() != b[6] :
        return False
    for i in range(1,n-5):
        if a[i] != b[i+6]:
            return False
    return True
            
def delete_info_zip(conn,file):
    with ZipFile(file+'.zip','r') as z: # liste des documents contenus dans le fichier zip
        for c in z.namelist():   
            country = c.split('.')[0]
            delete_country(conn,str(country))
            
conn = sqlite3.connect('pays.sqlite')
c=conn.cursor()
c.execute("""DROP TABLE countries""")
c.execute("""CREATE TABLE `countries` (              -- la table est nommé "countries"
	`wp`	TEXT NOT NULL UNIQUE,       -- nom de la page wikipédia, non nul, unique
    `name`	TEXT,                       -- nom complet du pays
	`capital`	TEXT,                   -- nom de la capitale
	`latitude`	REAL,                   -- latitude, champ numérique à valeur décimale
	`longitude`	REAL,                   -- longitude, champ numérique à valeur décimale
	`area`      REAL,
    `population`  INTEGER,
    `population_year`  INTEGER,
    `continent`    TEXT,
    `flag`      TEXT,
    `currency`  TEXT,
    `link`      TEXT,
    PRIMARY KEY(`wp`)                   -- wp est la clé primaire
);""")
save_info_zip(conn,"south_america")
save_info_zip(conn,"oceania")
                