import sqlite3

class Database():
  
  # Definir le constructeur de la classe
  def __init__(self):
    self.connection = None
  
  # Definir une connexion avec la base de données
  # Dans notre cas c'est la base de données créée à partir du script sql donné
  def get_connection(self):
    if self.connection is None:
      self.connection = sqlite3.connect("db/database.db")
    return self.connection

  # Deconnexion de la base de données
  def disconnect(self):
    if self.connection is not None:
      self.connection.close()
      self.connection = None

  def get_all_data(self):
    # On commence par defenir un curseur pour etablir la connextion
    # avec la base de données et effectuer les requettes necessaires
    cursor = self.get_connection().cursor()
    # On execute la requete de recherche
    cursor.execute("SELECT * FROM etherum")
    # On range toutes les données dans des variables
    for row in cursor:
      id, time, prices, volume, candle_closed, price_variation, total_price_variation = row
      # On affiche le résultat à la console
      print("Donnée n: %d Prices: %.2f Volue: %.2f Candle closed: %s Price variation: %2.f Total price variation: %2.f\n" %(id, prices, volume, candle_closed, price_variation, total_price_variation))


  def insert_data(self, time, prices, volume, candle_closed, price_variation, total_price_variation):
    connection = self.get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO etherum (info_date, prices, volume, candle_closed, price_variation, total_price_variation)" "VALUES(?,?,?,?,?,?)", (time, prices, volume, candle_closed, price_variation,total_price_variation))
    connection.commit()
