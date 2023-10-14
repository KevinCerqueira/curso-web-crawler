import requests
from bs4 import BeautifulSoup
import json
import time
import schedule
from datetime import datetime
from database import Database
from dotenv import load_dotenv
import os
from bot import BOT
# 1 https://www.kabum.com.br/gamer?page_number=1&page_size=20&facet_filters=&sort=most_searched
# 2 https://www.amazon.com.br/s?rh=n%3A7791985011&fs=true&ref=lp_7791985011_sar
# 3 https://www.magazineluiza.com.br/games/l/ga/

class Crawler:

	def __init__(self):
		load_dotenv()
		self.db = Database()
		self.bot = BOT()

	def request_data(self, url: str, retry: bool = False) -> BeautifulSoup:
		try:
			response = requests.get(url)
			soup = BeautifulSoup(response.text, 'html.parser')
			return soup
		except Exception as e:
			if not retry:
				time.sleep(3)
				return self.request_data(url, True)
			else:
				raise e

	@staticmethod
	def format_price(price: str) -> float:
		return float(price.replace('R$', '').replace('.', '').replace(',', '.'))

	def extract_from_kabum(self, page: int = 1, retry: bool = False) -> None:
		request = self.request_data(
			os.getenv('KABUM') + f'/gamer?facet_filters=&sort=most_searched&page_size=20&page_number={page}'
		)

		products = request.find_all('div', {'class': 'productCard'})
		if products is None:
			if not retry:
				time.sleep(3)
				self.extract_from_kabum(retry=True)
		else:
			for product in products:
				title = product.find('span', {'class': 'nameCard'}).text

				link = os.getenv('KABUM') + str(product.find('a', {'class': 'productLink'}).attrs['href'])
				second_request = self.request_data(link)

				price = second_request.find("h4", {"class": "finalPrice"}).text
				price = self.format_price(price)

				image = second_request.find_all("script")[1].text.replace('\\\\"', '')
				image = json.loads(image)["image"]

				data = {
					'title': title,
					'image': image,
					'price': price,
					'link': link,
					'date': datetime.now()
				}

				response = self.db.insert(data)
				if response is not None:
					if "old_price" in response:
						response["old_price"] = 0
					self.bot.post(response)

	def extract_from_amazon(self, page: int = 1, retry: bool = False) -> None:
		request = self.request_data(
			os.getenv('AMAZON') + f'/s?rh=n%3A7791985011&fs=true&ref=lp_7791985011_sar&{page}'
		)
		products = request.find_all("div", {"class": "s-card-container"})

		if products is None:
			if not retry:
				time.sleep(3)
				self.extract_from_amazon(retry=True)
		else:
			for product in products:
				title = product.find("span", {"class": "a-size-medium a-color-base a-text-normal"}).text
				link = os.getenv('AMAZON') + product.find("a", {
					"class": "a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"}
					).attrs["href"]

				span_price = product.find("span", {"class": "a-price"})
				price = span_price.find("span", {"class": "a-offscreen"}).text
				price = self.format_price(price)

				image = product.find("img", {"class": "s-image"}).text

				data = {
					'title': title,
					'image': image,
					'price': price,
					'link': link,
					'date': datetime.now()
				}

				response = self.db.insert(data)
				if response is not None:
					if "old_price" in response:
						response["old_price"] = 0
					self.bot.post(response)

	def execute(self, num_pages: int = 1):
		for page in range(1, num_pages):
			self.extract_from_kabum(page)
			self.extract_from_amazon(page)
			exit()

if __name__ == "__main__":
	crawler = Crawler()
	crawler.execute(2)

	def job():
		print("\n Execute job. Time: {}".format(str(datetime.now())))
		crawler.execute()

	schedule.every(1).minutes.do(job)

	while True:
		schedule.run_pending()
