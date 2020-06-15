# TD3-s7.py

import http.server
import socketserver
import sqlite3
import json

from urllib.parse import urlparse, parse_qs, unquote

#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  # version du serveur
  server_version = 'serveur.py/0.1'

  #
  # On surcharge la méthode qui traite les requêtes GET
  #
  def do_GET(self):
    # on récupère les paramètres
    self.init_params()

    # le chemin d'accès commence par /time
    if self.path.startswith('/time'):
      self.send_time()

    elif self.path_info[0] == 'service' and self.path_info[1] == 'countries' and len(self.path_info) > 1:
      continent = self.path_info[2] if len(self.path_info) > 2 else None
      self.send_json_countries(continent)

    # le chemin d'accès commence par /service/country/...
    elif self.path_info[0] == 'service' and self.path_info[1] == 'country' and len(self.path_info) > 2:
      self.send_json_country(self.path_info[2])

    # ou pas...
    else:
      self.send_static()

  #
  # On surcharge la méthode qui traite les requêtes HEAD
  #
  def do_HEAD(self):
    self.send_static()

  #
  # On envoie le document statique demandé
  #
  def send_static(self):

    # on modifie le chemin d'accès en insérant un répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)
        

  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.query_string = info.query
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
    else:
      self.body = ''
   
    # traces
    print('path_info =',self.path_info)
    print('body =',length,ctype,self.body)
    print('params =', self.params)


  #
  # On envoie un document avec l'heure
  #
  def send_time(self):
    # on récupère l'heure
    time = self.date_time_string()
    # on génère un document au format html
    body = '<!doctype html>' + \
           '<meta charset="utf-8">' + \
           '<title>l\'heure</title>' + \
           '<div>Voici l\'heure du serveur :</div>' + \
           '<pre>{}</pre>'.format(time)
    # pour prévenir qu'il s'agit d'une ressource au format html
    headers = [('Content-Type','text/html;charset=utf-8')]
    # on envoie
    self.send(body,headers)


  # On renvoie la liste des pays avec leurs coordonnées
  def send_json_countries(self,continent):
    # on récupère la liste de pays depuis la base de données
    r = self.db_get_countries(continent)
    # on renvoie une liste de dictionnaires au format JSON
    data = [ {k:a[k] for k in a.keys()} for a in r]
    print('data里是什么',data)
    json_data = json.dumps(data, indent=4)
    headers = [('Content-Type','application/json')]
    self.send(json_data,headers)
  #
  # On renvoie les informations d'un pays au format json
  #
  def send_json_country(self,country):
    # on récupère le pays depuis la base de données
    r = self.db_get_country(country)
    # on n'a pas trouvé le pays demandé
    if r == None:
      self.send_error(404,'Country not found')
    # on renvoie un dictionnaire au format JSON
    else:
      data = {k:r[k] for k in r.keys()}
      json_data = json.dumps(data, indent=4)
      headers = [('Content-Type','application/json')]
      self.send(json_data,headers)

  #
  # Récupération de la liste des pays depuis la base
  #
  def db_get_countries(self,continent=None):
    c = conn.cursor()
    # ajouter nouvelles données
    sql = 'SELECT wp, capital, latitude, longitude,population,population_year,continent,flag,currency from countries'
    # les pays d'un continent
    if continent:
      sql += ' WHERE continent LIKE ?'
      c.execute(sql,('%{}%'.format(continent),))
    # tous les pays de la base
    else:
      c.execute(sql)
    return c.fetchall()

  #
  # Récupération d'un pays dans la base
  #
  def db_get_country(self,country):
    # préparation de la requête SQL
    c = conn.cursor()
    sql = 'SELECT * from countries WHERE wp=?'
    # récupération de l'information (ou pas)
    c.execute(sql, (country,))
    return c.fetchone()

  #
  # On envoie les entêtes et le corps fourni
  #
  def send(self,body,headers=[]):

    # on encode la chaine de caractères à envoyer
    encoded = bytes(body, 'UTF-8')

    self.send_raw(encoded,headers)

  def send_raw(self,data,headers=[]):
    # on envoie la ligne de statut
    self.send_response(200)

    # on envoie les lignes d'entête et la ligne vide
    [self.send_header(*t) for t in headers]
    self.send_header('Content-Length',int(len(data)))
    self.end_headers()

    # on envoie le corps de la réponse
    self.wfile.write(data)

 
#
# Ouverture d'une connexion avec la base de données
#
conn = sqlite3.connect('pays.sqlite')

# Pour accéder au résultat des requêtes sous forme d'un dictionnaire
conn.row_factory = sqlite3.Row

#
# Instanciation et lancement du serveur
#
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()

