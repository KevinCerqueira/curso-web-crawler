from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os

class Database:
	
	def __init__(self):
		load_dotenv()
		self.offers = self.connect()
	
	def connect(self):
		client = MongoClient(os.getenv('DB_URI'))
		db = client['curso']
		return db.offers
	
	def insert(self, data: dict) -> dict | None:
		query = {'title': data['title']}
		result = self.offers.find_one(query, sort=[('date', -1)])

		if result is None:
			self.offers.insert_one(data)
			return data
		elif result['price'] > data['price'] or result['price'] < data['price']:
			product = data.copy()
			product["old_price"] = result["price"]
			self.offers.insert_one(data)
			return product
		else:
			return None
			

if __name__ == "__main__":
    db = Database()
    data = {'title': 'Console Microsoft Xbox Series S, 512GB, Branco - RRS-00006', 'image': 'https://images.kabum.com.br/produtos/fotos/sync_mirakl/200089/Console-Microsoft-Xbox-Series-S-512GB-Branco-RRS-00006_1696533531_gg.jpg', 'price': 2085.4, 'link': 'https://www.kabum.com.br/produto/200089/console-microsoft-xbox-series-s-512gb-branco-rrs-00006'}
    db.insert(data)